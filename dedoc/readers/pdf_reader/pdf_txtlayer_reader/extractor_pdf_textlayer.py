import binascii
import itertools
import logging
import os
import re
import uuid
from collections import namedtuple
from typing import List, IO, Tuple, Match, Optional
import cv2
import numpy as np
from PIL import Image

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.style_annotation import StyleAnnotation
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTAnno, LTTextBoxHorizontal, LTTextLineHorizontal, LTContainer, LTRect, \
    LTFigure, LTImage, LTCurve, LTTextBox
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage

from dedoc.utils.pdf_utils import get_page_image
from dedoc.data_structures.bbox import BBox
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.location import Location
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox

StyleLine = namedtuple("StyleLine", ["begin", "end", "bold", "italic", "font_size", "font_style", "table_name"])


class ExtractorPdfTextLayer(object):
    """
    Class extarcts text with style from pdf with help pdfminer.six
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__()
        self.config = config
        self.logger = self.config.get("logger", logging.getLogger())

    def extract_text_layer(self, path: str, page_number: int, is_one_column_document: bool) -> Optional[PageWithBBox]:
        """
        Extract text information with metadata from pdf with help pdfminer.six
        :param path: path to pdf
        :return: pages_with_bbox - page with extracted text
        """
        with open(path, 'rb') as fp:
            pages = PDFPage.get_pages(fp)
            for page_num, page in enumerate(pages):
                if page_num != page_number:
                    continue
                return self.__handle_page(page=page, page_number=page_number, path=path,
                                          is_one_column_document=is_one_column_document)

    def __handle_page(self, page: PDFPage, page_number: int, path: str, is_one_column_document: bool) -> PageWithBBox:
        directory = os.path.dirname(path)
        device, interpreter = self.__get_interpreter(is_one_column_document=is_one_column_document)
        try:
            interpreter.process_page(page)
        except Exception as e:
            raise BadFileFormatException("can't handle file {} get {}".format(path, e))

        layout = device.get_result()
        image_page = self.__get_image(path=path, page_num=page_number)
        image_height, image_width, *_ = image_page.shape

        height = page.mediabox[3]
        width = page.mediabox[2]
        if height > 0 and width > 0:
            k_w, k_h = image_width / width, image_height / height
            page_broken = False
        else:
            page_broken = True
            k_w, k_h = None, None
        # 1. extract only textline object
        images = []
        layout_objects = [lobj for lobj in layout]
        lobjs_textline = []
        for lobj in layout_objects:
            if isinstance(lobj, LTTextBoxHorizontal):
                lines = [lobj_text for lobj_text in lobj if isinstance(lobj_text, LTTextLineHorizontal)]
                lines.sort(key=lambda lobj: float(height - lobj.y1))
                lobjs_textline.extend(lines)
            elif isinstance(lobj, LTTextLineHorizontal):
                lobjs_textline.append(lobj)
            elif isinstance(lobj, LTFigure) and not page_broken:
                attachment = self.__extract_image(directory, height, image_page, k_h, k_w, lobj, page_number)

                if attachment is not None:
                    images.append(attachment)

        bboxes = []
        for line_num, lobj in enumerate(lobjs_textline):
            bbox = self.get_info_layout_object(lobj,
                                               page_num=page_number,
                                               line_num=line_num,
                                               k_w=k_w,
                                               k_h=k_h,
                                               height=height)

            if bbox.bbox.width * bbox.bbox.height > 0:
                bboxes.append(bbox)
        attachments = images if len(images) < 10 else []
        return PageWithBBox(bboxes=bboxes, image=image_page, page_num=page_number, attachments=attachments)

    def __extract_image(self,
                        directory: str,
                        height: int,
                        image_page: np.ndarray,
                        k_h: float,
                        k_w: float,
                        lobj: LTContainer,
                        page_number: int) -> Optional[PdfImageAttachment]:
        try:
            bbox = self._create_bbox(k_h=k_h, k_w=k_w, height=height, lobj=lobj)
            location = Location(bbox=bbox, page_number=page_number)
            cropped = image_page[bbox.y_top_left: bbox.y_bottom_right, bbox.x_top_left: bbox.x_bottom_right]
            uid = "fig_{}".format(uuid.uuid1())
            file_name = "{}.png".format(uid)
            path_out = os.path.join(directory, file_name)
            Image.fromarray(cropped).save(path_out)
            image_page[bbox.y_top_left: bbox.y_bottom_right, bbox.x_top_left: bbox.x_bottom_right] = 255
            attachment = PdfImageAttachment(original_name=file_name,
                                            tmp_file_path=path_out,
                                            need_content_analysis=False,
                                            uid=uid,
                                            location=location)
        except Exception as ex:
            self.logger.error(ex)
            attachment = None

        return attachment

    @staticmethod
    def __get_image(path: str, page_num: int) -> np.ndarray:
        image_page = np.array(get_page_image(path=path, page_id=page_num))  # noqa
        image_page = np.array(image_page)
        if len(image_page.shape) == 2:
            image_page = cv2.cvtColor(image_page, cv2.COLOR_GRAY2BGR)
        return image_page

    def __get_interpreter(self, is_one_column_document: bool) -> Tuple[PDFPageAggregator, PDFPageInterpreter]:
        rsrcmgr = PDFResourceManager()
        if is_one_column_document is not None and is_one_column_document:
            laparams = LAParams(line_margin=3.0, line_overlap=0.1, boxes_flow=0.5, word_margin=1.5, char_margin=100.0,
                                detect_vertical=False)
        else:
            laparams = LAParams(line_margin=1.5, line_overlap=0.5, boxes_flow=0.5, word_margin=0.1,
                                detect_vertical=False)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        return device, interpreter

    def __debug_extract_layout(self,
                               image_src: np.ndarray,
                               layout: LTContainer,
                               page_num: int,
                               k_w: float,
                               k_h: float,
                               page: PDFPage) -> None:
        """
        Function for debugging of pdfminer.six layout
        :param layout: container of layout element
        :return: None
        """
        tmp_dir = os.path.join(self.config["path_debug"], "pdfminer")
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

        file_text = open(os.path.join(tmp_dir, "text_{}.txt".format(page_num)), "wt")

        # 1. extract layout objects
        lobjs = [lobj for lobj in layout]
        lobjs_textline = []
        lobjs_box = []
        lobjs_words = []
        lobjs_figures = []
        lobjs_images = []
        lobjs_curves = []

        for lobj in lobjs:
            if isinstance(lobj, LTTextBoxHorizontal):
                lobjs_textline.extend(lobj)
            elif isinstance(lobj, LTTextLineHorizontal):
                lobjs_textline.append(lobj)
            elif isinstance(lobj, LTRect):
                lobjs_box.append(lobj)
            elif isinstance(lobj, LTFigure):
                lobjs_figures.append(lobj)
            elif isinstance(lobj, LTImage):
                lobjs_images.append(lobj)
            elif isinstance(lobj, LTCurve):
                lobjs_curves.append(lobj)
            elif isinstance(lobj, LTTextBox):
                lobjs_words.append(lobj)

        # 3. print information
        self.__draw_layout_element(image_src, lobjs_textline, file_text, k_w, k_h, page, (0, 255, 0))
        self.__draw_layout_element(image_src, lobjs_words, file_text, k_w, k_h, page, (0, 255, 0))
        self.__draw_layout_element(image_src, lobjs_box, file_text, k_w, k_h, page, (0, 0, 255), text="LTRect")
        self.__draw_layout_element(image_src, lobjs_figures, file_text, k_w, k_h, page, (255, 0, 0), text="LTFigure")
        self.__draw_layout_element(image_src, lobjs_images, file_text, k_w, k_h, page, (0, 255, 255), text="LTImage")
        self.__draw_layout_element(image_src, lobjs_curves, file_text, k_w, k_h, page, (0, 255, 255), text="LTCurve")

        cv2.imwrite(os.path.join(tmp_dir, "img_page_{}.png".format(page_num)), image_src)
        file_text.close()

    def __draw_layout_element(self,
                              image_src: np.ndarray,
                              lobjs: List,
                              file: IO,
                              k_w: float,
                              k_h: float,
                              page: PDFPage,
                              color: Tuple[int, int, int],
                              text: Optional[str] = None) -> None:
        for line_num, lobj in enumerate(lobjs):
            # converting coordinate from pdf format into image
            box_lobj = ExtractorPdfTextLayer.convert_coordinates_pdf_to_image(lobj, k_w, k_h, page.mediabox[3])

            cv2.rectangle(image_src,
                          (box_lobj.x_top_left, box_lobj.y_top_left),
                          (box_lobj.x_bottom_right, box_lobj.y_bottom_right), color)

            if text is not None:
                cv2.putText(image_src, text, (box_lobj.x_top_left, box_lobj.y_top_left), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            color)
            else:
                file.write(lobj.get_text())

    @staticmethod
    def convert_coordinates_pdf_to_image(lobj: LTContainer, k_w: float, k_h: float, height_page: int) -> BBox:
        x0_new = int(lobj.x0 * k_w)
        x1_new = int(lobj.x1 * k_w)
        y0_new = int((height_page - lobj.y1) * k_h)
        y1_new = int((height_page - lobj.y0) * k_h)

        return BBox(x0_new, y0_new, x1_new - x0_new, y1_new - y0_new)

    def get_info_layout_object(self,
                               lobj: LTContainer,
                               page_num: int,
                               line_num: int,
                               k_w: float,
                               k_h: float,
                               height: int) -> TextWithBBox:
        # 1 - converting coordinate from pdf format into image
        bbox = self._create_bbox(height, k_h, k_w, lobj)
        # 2 - extract text and text annotations from current object
        text, text_anns = self._get_style_and_text_from_layout_object(lobj)
        return TextWithBBox(bbox=bbox, page_num=page_num, text=text, line_num=line_num, annotations=text_anns)

    def _create_bbox(self, height: int, k_h: float, k_w: float, lobj: LTContainer) -> BBox:
        curr_box_line = ExtractorPdfTextLayer.convert_coordinates_pdf_to_image(lobj, k_w, k_h, height)
        bbox = BBox.from_two_points((curr_box_line.x_top_left, curr_box_line.y_top_left),
                                    (curr_box_line.x_bottom_right, curr_box_line.y_bottom_right))
        return bbox

    def _get_style_and_text_from_layout_object(self, lobj: LTContainer) -> [str, List[Annotation]]:

        if isinstance(lobj, LTTextLineHorizontal):
            # cleaning text from (cid: *)
            text = self._cleaning_text_from_hieroglyphics(lobj.get_text())
            # get line's style
            anns = self._get_line_style(lobj)

            return text, anns
        else:
            return "", None

    def _get_line_style(self, lobj: LTTextLineHorizontal) -> List[Annotation]:
        # 1 - prepare data for groupby name
        chars_with_style = []
        rand_weight = self._get_new_weight()
        prev_style = ""
        for item, lobj_char in enumerate(lobj):
            if isinstance(lobj_char, LTChar) or isinstance(lobj_char, LTAnno):
                if len(chars_with_style) > 0:
                    # check next char different from previously then we fresh rand_weight
                    prev_style, prev_size = chars_with_style[-1].split('_rand_')
                if isinstance(lobj_char, LTChar):
                    curr_style = "{}_{}".format(lobj_char.fontname, round(lobj_char.size, 0))

                    if curr_style != prev_style:
                        rand_weight = self._get_new_weight()

                    chars_with_style.append("{}_rand_{}".format(curr_style, rand_weight))
                elif isinstance(lobj_char, LTAnno) \
                        and lobj_char.get_text() in (' ', '\n') \
                        and len(chars_with_style) > 0:
                    # check on the space or \n (in pdfminer is type LTAnno)
                    # duplicated previous style
                    chars_with_style.append(chars_with_style[-1])

        styles = []

        # 2 - extract diapasons from the style char array (chars_with_style)
        pointer_into_string = 0

        for key, group in itertools.groupby(chars_with_style, lambda x: x):
            count_chars = len(list(group))
            styles.extend(self.__parse_style_string(key, pointer_into_string, pointer_into_string + count_chars - 1))
            pointer_into_string += count_chars

        return styles

    def _cleaning_text_from_hieroglyphics(self, text_str: str) -> str:
        """
        replace all cid-codecs into ascii symbols. cid-encoding - hieroglyphic fonts
        :param text_str: text
        :return: text wo cids-chars
        """
        return re.sub(r"\(cid:(\d)*\)", self.cid_recognized, text_str)

    def cid_recognized(self, m: Match) -> str:
        v = m.group(0)
        v = v.strip('(')
        v = v.strip(')')
        ascii_num = v.split(':')[-1]
        ascii_num = int(ascii_num)
        text_val = chr(ascii_num)

        return text_val

    def _get_new_weight(self) -> str:
        return binascii.hexlify(os.urandom(8)).decode('ascii')

    def __parse_style_string(self, chars_with_meta: str, begin: int, end: int) -> List[Annotation]:
        # style parsing
        line_anns = []
        prev_style, _ = chars_with_meta.split('_rand_')
        font, size, *_ = prev_style.split('_')
        fontname_wo_rand = font.split('+')[-1]
        styles = fontname_wo_rand.split('-')[-1]
        if "Bold" in styles:
            line_anns.append(BoldAnnotation(begin, end, value="True"))
        if "Italic" in styles:
            line_anns.append(ItalicAnnotation(begin, end, value="True"))
        line_anns.append(StyleAnnotation(begin, end, value=fontname_wo_rand))
        if size.replace('.', '', 1).isnumeric():
            line_anns.append(SizeAnnotation(begin, end, value=size))

        return line_anns
