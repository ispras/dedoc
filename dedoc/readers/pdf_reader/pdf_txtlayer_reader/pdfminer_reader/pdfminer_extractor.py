import binascii
import itertools
import logging
import os
import uuid
from collections import namedtuple
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTAnno, LTChar, LTContainer, LTCurve, LTFigure, LTImage, LTRect
from pdfminer.layout import LTTextBox, LTTextBoxHorizontal, LTTextContainer, LTTextLineHorizontal
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.style_annotation import StyleAnnotation
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.location import Location
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdfminer_reader.pdfminer_utils import cleaning_text_from_hieroglyphics, create_bbox, draw_annotation
from dedoc.utils.pdf_utils import get_page_image

logging.getLogger("pdfminer").setLevel(logging.ERROR)
WordObj = namedtuple("Word", ["start", "end", "value"])


class PdfminerExtractor(object):
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
        with open(path, "rb") as fp:
            pages = PDFPage.get_pages(fp)
            for page_num, page in enumerate(pages):
                if page_num != page_number:
                    continue
                return self.__handle_page(page=page, page_number=page_number, path=path, is_one_column_document=is_one_column_document)

    def __handle_page(self, page: PDFPage, page_number: int, path: str, is_one_column_document: bool) -> PageWithBBox:
        directory = os.path.dirname(path)
        device, interpreter = self.__get_interpreter(is_one_column_document=is_one_column_document)
        try:
            interpreter.process_page(page)
        except Exception as e:
            raise BadFileFormatError(f"can't handle file {path} get {e}")

        layout = device.get_result()
        image_page = self.__get_image(path=path, page_num=page_number)
        image_height, image_width, *_ = image_page.shape

        height = int(page.mediabox[3])
        width = int(page.mediabox[2])
        if height > 0 and width > 0:
            k_w, k_h = image_width / page.mediabox[2], image_height / page.mediabox[3]
            page_broken = False
        else:
            page_broken = True
            k_w, k_h = None, None

        if self.config.get("debug_mode", False):
            self.__debug_extract_layout(image_page, layout, page_number, k_w, k_h, page, width, height)

        # 1. extract textline objects and image (as LTImage)
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
            text_with_bbox = self.get_info_layout_object(lobj, page_num=page_number, line_num=line_num, k_w=k_w, k_h=k_h, height=height, width=width)
            if text_with_bbox.bbox.width * text_with_bbox.bbox.height > 0:
                bboxes.append(text_with_bbox)

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
            bbox = create_bbox(k_h=k_h, k_w=k_w, height=height, lobj=lobj)
            location = Location(bbox=bbox, page_number=page_number)
            cropped = image_page[bbox.y_top_left: bbox.y_bottom_right, bbox.x_top_left: bbox.x_bottom_right]
            uid = f"fig_{uuid.uuid1()}"
            file_name = f"{uid}.png"
            path_out = os.path.join(directory, file_name)
            Image.fromarray(cropped).save(path_out)
            attachment = PdfImageAttachment(original_name=file_name, tmp_file_path=path_out, need_content_analysis=False, uid=uid, location=location)
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
            laparams = LAParams(line_margin=3.0, line_overlap=0.1, boxes_flow=0.5, word_margin=1.5, char_margin=100.0, detect_vertical=False)
        else:
            laparams = LAParams(line_margin=1.5, line_overlap=0.5, boxes_flow=0.5, word_margin=0.1, detect_vertical=False)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        return device, interpreter

    def get_info_layout_object(self,
                               lobj: LTContainer,
                               page_num: int,
                               line_num: int,
                               k_w: float,
                               k_h: float,
                               height: int,
                               width: int) -> TextWithBBox:
        # 1 - converting coordinate from pdf format into image
        bbox = create_bbox(height, k_h, k_w, lobj)
        # 2 - extract text and text annotations from current object
        text = ""
        annotations = []
        if isinstance(lobj, LTTextLineHorizontal):
            # cleaning text from (cid: *)
            text = cleaning_text_from_hieroglyphics(lobj.get_text())
            # get line's annotations
            annotations = self.__get_line_annotations(lobj, k_w, k_h, height, width)

        return TextWithBBox(bbox=bbox, page_num=page_num, text=text, line_num=line_num, annotations=annotations)

    def __get_line_annotations(self, lobj: LTTextLineHorizontal, k_w: float, k_h: float, height: int, width: int) -> List[Annotation]:
        # 1 - prepare data for group by name
        chars_with_style = []
        rand_weight = self._get_new_weight()
        prev_style = ""

        for lobj_char in lobj:
            if isinstance(lobj_char, LTChar) or isinstance(lobj_char, LTAnno):
                # get styles
                if len(chars_with_style) > 0:
                    # check next char different from previously then we fresh rand_weight
                    prev_style, prev_size = chars_with_style[-1].split("_rand_")

                if isinstance(lobj_char, LTChar) and lobj_char.get_text() not in (" ", "\n", "\t"):
                    curr_style = f"{lobj_char.fontname}_{round(lobj_char.size, 0)}"

                    if curr_style != prev_style:
                        rand_weight = self._get_new_weight()

                    chars_with_style.append(f"{curr_style}_rand_{rand_weight}")
                elif lobj_char.get_text() in (" ", "\n", "\t") and len(chars_with_style) > 0:
                    # check on the space or \n
                    # duplicated previous style
                    chars_with_style.append(chars_with_style[-1])

        annotations = self.__extract_words_bbox_annotation(lobj, k_w, k_h, height, width)
        # 3 - extract range from chars_with_style array
        char_pointer = 0

        for key, group in itertools.groupby(chars_with_style, lambda x: x):
            count_chars = len(list(group))
            annotations.extend(self.__parse_style_string(key, char_pointer, char_pointer + count_chars - 1))
            char_pointer += count_chars

        return annotations

    def __extract_words_bbox_annotation(self, lobj: LTTextContainer, k_w: float, k_h: float, height: int, width: int) -> List[Annotation]:
        words: List[WordObj] = []
        word: WordObj = WordObj(start=0, end=0, value=LTTextContainer())
        if isinstance(lobj, LTTextLineHorizontal):
            lobj = [lobj]

        for text_line in lobj:
            for item, lobj_char in enumerate(text_line):
                if isinstance(lobj_char, LTChar) and lobj_char.get_text() not in (" ", "\n", "\t"):
                    word = word._replace(end=word.end + 1)
                    word.value.add(lobj_char)
                elif lobj_char.get_text() in (" ", "\n", "\t"):
                    if word.value._objs:
                        words.append(word)
                    word = WordObj(start=item + 1, end=item + 1, value=LTTextContainer())

        annotations = [BBoxAnnotation(start=word.start,
                                      end=word.end,
                                      value=create_bbox(height=height, k_h=k_h, k_w=k_w, lobj=word.value),
                                      page_width=width,
                                      page_height=height) for word in words]
        return annotations

    def _get_new_weight(self) -> str:
        return binascii.hexlify(os.urandom(8)).decode("ascii")

    def __parse_style_string(self, chars_with_meta: str, begin: int, end: int) -> List[Annotation]:
        # style parsing
        annotations = []
        prev_style, _ = chars_with_meta.split("_rand_")
        font, size, *_ = prev_style.split("_")
        fontname_wo_rand = font.split("+")[-1]
        styles = fontname_wo_rand.split("-")[-1]
        annotations.append(StyleAnnotation(begin, end, value=fontname_wo_rand))

        if "Bold" in styles:
            annotations.append(BoldAnnotation(begin, end, value="True"))
        if "Italic" in styles:
            annotations.append(ItalicAnnotation(begin, end, value="True"))

        if size.replace(".", "", 1).isnumeric():
            annotations.append(SizeAnnotation(begin, end, value=size))

        return annotations

    def __debug_extract_layout(self, image_src: np.ndarray, layout: LTContainer, page_num: int, k_w: float, k_h: float, page: PDFPage,
                               width: int, height: int) -> None:
        """
        Function for debugging of pdfminer.six layout
        :param layout: container of layout element
        :return: None
        """
        tmp_dir = os.path.join(self.config.get("path_debug"), "pdfminer")
        os.makedirs(tmp_dir, exist_ok=True)

        file_text = open(os.path.join(tmp_dir, f"text_{page_num}.txt"), "wt")

        # 1. extract layout objects
        lobjs = [lobj for lobj in layout]
        lobjs_textline = []
        lobjs_box = []
        lobjs_words = []
        lobjs_figures = []
        lobjs_images = []
        lobjs_curves = []
        annotations = []

        for lobj in lobjs:
            if isinstance(lobj, LTTextBoxHorizontal):
                annotations.extend(self.__extract_words_bbox_annotation(lobj, k_w, k_h, height, width))
                lobjs_textline.extend(lobj)
            elif isinstance(lobj, LTTextLineHorizontal):
                annotations.extend(self.__extract_words_bbox_annotation(lobj, k_w, k_h, height, width))
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
        draw_annotation(image_src, annotations)
        """
        Call for debugging other LT elements:
        self.__draw_layout_element(image_src, lobjs_textline, file_text, k_w, k_h, page, (0, 255, 0))
        self.__draw_layout_element(image_src, lobjs_words, file_text, k_w, k_h, page, (0, 255, 0))
        self.__draw_layout_element(image_src, lobjs_box, file_text, k_w, k_h, page, (0, 0, 255), text="LTRect")
        self.__draw_layout_element(image_src, lobjs_figures, file_text, k_w, k_h, page, (255, 0, 0), text="LTFigure")
        self.__draw_layout_element(image_src, lobjs_images, file_text, k_w, k_h, page, (0, 255, 255), text="LTImage")
        self.__draw_layout_element(image_src, lobjs_curves, file_text, k_w, k_h, page, (0, 255, 255), text="LTCurve")'''
        """
        cv2.imwrite(os.path.join(tmp_dir, f"img_page_{page_num}.png"), image_src)
        file_text.close()
