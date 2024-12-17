from abc import abstractmethod
from collections import namedtuple
from typing import Dict, Iterator, List, Optional, Set, Tuple

from dedocutils.data_structures.bbox import BBox
from numpy import ndarray

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable


ParametersForParseDoc = namedtuple("ParametersForParseDoc", [
    "is_one_column_document",
    "document_orientation",
    "language",
    "need_header_footers_analysis",
    "need_pdf_table_analysis",
    "first_page",
    "last_page",
    "need_binarization",
    "table_type",
    "with_attachments",
    "attachments_dir",
    "need_content_analysis",
    "need_gost_frame_analysis",
    "pdf_with_txt_layer"
])


class PdfBaseReader(BaseReader):
    """
    Base class for pdf documents parsing.
    """

    def __init__(self, *, config: Optional[dict] = None, recognized_extensions: Optional[Set[str]] = None, recognized_mimes: Optional[Set[str]] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions, recognized_mimes=recognized_mimes)

        from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.metadata_extractor import LineMetadataExtractor
        from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.scan_paragraph_classifier_extractor import ScanParagraphClassifierExtractor
        from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.gost_frame_recognizer import GOSTFrameRecognizer
        from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer
        from dedoc.readers.pdf_reader.utils.line_object_linker import LineObjectLinker
        from dedoc.attachments_extractors.concrete_attachments_extractors.pdf_attachments_extractor import PDFAttachmentsExtractor

        self.config["n_jobs"] = self.config.get("n_jobs", 1)
        self.table_recognizer = TableRecognizer(config=self.config)
        self.metadata_extractor = LineMetadataExtractor(config=self.config)
        self.attachment_extractor = PDFAttachmentsExtractor(config=self.config)
        self.linker = LineObjectLinker(config=self.config)
        self.paragraph_extractor = ScanParagraphClassifierExtractor(config=self.config)
        self.gost_frame_recognizer = GOSTFrameRecognizer(config=self.config)

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`
        (``can_be_multiline`` attribute is important for paragraph extraction).
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.

        You can also see :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.
        """
        import dedoc.utils.parameter_utils as param_utils

        parameters = {} if parameters is None else parameters
        first_page, last_page = param_utils.get_param_page_slice(parameters)

        params_for_parse = ParametersForParseDoc(
            language=param_utils.get_param_language(parameters),
            is_one_column_document=param_utils.get_param_is_one_column_document(parameters),
            document_orientation=param_utils.get_param_document_orientation(parameters),
            need_header_footers_analysis=param_utils.get_param_need_header_footers_analysis(parameters),
            need_pdf_table_analysis=param_utils.get_param_need_pdf_table_analysis(parameters),
            first_page=first_page,
            last_page=last_page,
            need_binarization=param_utils.get_param_need_binarization(parameters),
            table_type=param_utils.get_param_table_type(parameters),
            with_attachments=param_utils.get_param_with_attachments(parameters),
            attachments_dir=param_utils.get_param_attachments_dir(parameters, file_path),
            need_content_analysis=param_utils.get_param_need_content_analysis(parameters),
            need_gost_frame_analysis=param_utils.get_param_need_gost_frame_analysis(parameters),
            pdf_with_txt_layer=param_utils.get_param_pdf_with_txt_layer(parameters)
        )

        lines, scan_tables, attachments, warnings, metadata = self._parse_document(file_path, params_for_parse)

        if params_for_parse.with_attachments and self.attachment_extractor.can_extract(file_path):
            attachments += self.attachment_extractor.extract(file_path=file_path, parameters=parameters)

        result = UnstructuredDocument(lines=lines, tables=scan_tables, attachments=attachments, warnings=warnings, metadata=metadata)
        return self._postprocess(result)

    def _parse_document(self, path: str, parameters: ParametersForParseDoc) -> (
            Tuple)[List[LineWithMeta], List[ScanTable], List[PdfImageAttachment], List[str], Optional[dict]]:
        import math
        from joblib import Parallel, delayed
        from dedoc.data_structures.hierarchy_level import HierarchyLevel
        from dedoc.readers.pdf_reader.utils.header_footers_analysis import footer_header_analysis
        from dedoc.utils.pdf_utils import get_pdf_page_count
        from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
        from dedoc.utils.utils import flatten

        first_page = 0 if parameters.first_page is None or parameters.first_page < 0 else parameters.first_page
        last_page = math.inf if parameters.last_page is None else parameters.last_page
        images = self._get_images(path, first_page, last_page)

        if parameters.need_gost_frame_analysis and isinstance(self, (PdfImageReader, PdfTxtlayerReader)):
            result, gost_analyzed_images = self._process_document_with_gost_frame(images=images, first_page=first_page, parameters=parameters, path=path)
        else:
            result = Parallel(n_jobs=self.config["n_jobs"])(
                delayed(self._process_one_page)(image, parameters, page_number, path) for page_number, image in enumerate(images, start=first_page)
            )

        page_count = get_pdf_page_count(path)
        page_count = math.inf if page_count is None else page_count
        if first_page > 0 or last_page < page_count:
            warnings = ["The document is partially parsed"]
            metadata = dict(first_page=first_page)
            if last_page != math.inf:
                metadata["last_page"] = last_page
        else:
            warnings = []
            metadata = {}

        if len(result) == 0:
            all_lines, unref_tables, attachments, page_angles = [], [], [], []
        else:
            all_lines, unref_tables, attachments, page_angles = map(list, map(flatten, zip(*result)))
        if parameters.need_header_footers_analysis:
            lines = [lines for lines, _, _, _ in result]
            lines, headers, footers = footer_header_analysis(lines)
            all_lines = list(flatten(lines))
        if parameters.need_gost_frame_analysis and isinstance(self, PdfImageReader):
            self._shift_all_contents(lines=all_lines, unref_tables=unref_tables, attachments=attachments, gost_analyzed_images=gost_analyzed_images)
        mp_tables = self.table_recognizer.convert_to_multipages_tables(unref_tables, lines_with_meta=all_lines)
        all_lines_with_links = self.linker.link_objects(lines=all_lines, tables=mp_tables, images=attachments)

        for line in all_lines_with_links:
            line.metadata.tag_hierarchy_level = HierarchyLevel.create_unknown()

        all_lines_with_paragraphs = self.paragraph_extractor.extract(all_lines_with_links)
        if page_angles:
            metadata["rotated_page_angles"] = page_angles
        return all_lines_with_paragraphs, mp_tables, attachments, warnings, metadata

    def _process_document_with_gost_frame(self, images: Iterator[ndarray], first_page: int, parameters: ParametersForParseDoc, path: str) -> \
            Tuple[Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment], List[float]], Dict[int, Tuple[ndarray, BBox, Tuple[int, ...]]]]:
        from joblib import Parallel, delayed
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader

        gost_analyzed_images = Parallel(n_jobs=self.config["n_jobs"])(delayed(self.gost_frame_recognizer.rec_and_clean_frame)(image) for image in images)
        page_range = range(first_page, first_page + len(gost_analyzed_images))
        gost_analyzed_images = dict(zip(page_range, gost_analyzed_images))
        if isinstance(self, PdfTxtlayerReader):
            self.gost_frame_boxes = dict(zip(page_range, [(item[1], item[2]) for item in gost_analyzed_images.values()]))
        result = Parallel(n_jobs=self.config["n_jobs"])(
            delayed(self._process_one_page)(image, parameters, page_number, path) for page_number, (image, box, original_image_shape) in
            gost_analyzed_images.items()
        )
        return result, gost_analyzed_images

    def _shift_all_contents(self, lines: List[LineWithMeta], unref_tables: List[ScanTable], attachments: List[PdfImageAttachment],
                            gost_analyzed_images: Dict[int, Tuple[ndarray, BBox, Tuple[int, ...]]]) -> None:
        # shift unref_tables
        for scan_table in unref_tables:
            for location in scan_table.locations:
                table_page_number = location.page_number
                location.shift(shift_x=gost_analyzed_images[table_page_number][1].x_top_left, shift_y=gost_analyzed_images[table_page_number][1].y_top_left)
            page_number = scan_table.locations[0].page_number
            for row in scan_table.cells:
                for cell in row:
                    image_width, image_height = gost_analyzed_images[page_number][2][1], gost_analyzed_images[page_number][2][0]
                    shift_x, shift_y = (gost_analyzed_images[page_number][1].x_top_left, gost_analyzed_images[page_number][1].y_top_left)
                    cell.shift(shift_x=shift_x, shift_y=shift_y, image_width=image_width, image_height=image_height)

        # shift attachments
        for attachment in attachments:
            attachment_page_number = attachment.location.page_number
            shift_x, shift_y = gost_analyzed_images[attachment_page_number][1].x_top_left, gost_analyzed_images[attachment_page_number][1].y_top_left
            attachment.location.shift(shift_x, shift_y)

        # shift lines
        for line in lines:
            page_number = line.metadata.page_id
            image_width, image_height = gost_analyzed_images[page_number][2][1], gost_analyzed_images[page_number][2][0]
            line.shift(shift_x=gost_analyzed_images[page_number][1].x_top_left,
                       shift_y=gost_analyzed_images[page_number][1].y_top_left,
                       image_width=image_width,
                       image_height=image_height)

    @abstractmethod
    def _process_one_page(self, image: ndarray, parameters: ParametersForParseDoc, page_number: int, path: str) \
            -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment], List[float]]:
        """
            function parses image and returns:
            - recognized textual lines with annotations
            - recognized tables on an image
            - attachments (figures on images)
            - [rotated_angle] - the angle by which the image was rotated for recognition
        """
        pass

    def _get_images(self, path: str, page_from: int, page_to: int) -> Iterator[ndarray]:
        import os
        import cv2
        from dedoc.extensions import recognized_extensions as extensions, recognized_mimes as mimes
        from dedoc.utils.utils import get_file_mime_by_content
        from dedoc.utils.utils import get_file_mime_type, splitext_

        mime = get_file_mime_type(path)
        mime = get_file_mime_by_content(path) if mime not in self._recognized_mimes else mime
        if mime in mimes.pdf_like_format:
            yield from self._split_pdf2image(path, page_from, page_to)
        elif mime in mimes.image_like_format or path.lower().endswith(tuple(extensions.image_like_format)):
            image = cv2.imread(path)
            if image is None:
                raise BadFileFormatError(f"seems file {os.path.basename(path)} not an image")
            yield image
        else:
            raise BadFileFormatError(f"Unsupported input format: {splitext_(path)[1]}")

    def _split_pdf2image(self, path: str, page_from: int, page_to: int) -> Iterator[ndarray]:
        if page_from >= page_to:
            return

        import math
        import os
        import numpy as np
        from pdf2image import convert_from_path
        from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
        from dedoc.utils.pdf_utils import get_pdf_page_count

        try:
            page_count = get_pdf_page_count(path)
            page_count = math.inf if page_count is None else page_count
            step = max(self.config["n_jobs"], 3)
            left = page_from + 1
            images = None
            while (images is None or len(images) > 0) and left <= min(page_to, page_count):
                right = left + step
                # for convert_from_path function first_page should start from 1, last_page is included to the result
                images = convert_from_path(path, first_page=left, last_page=right)
                # in logging we include both ends of the pages interval, numeration starts with 1
                self.logger.info(f"Get page from {left} to {min(right, page_count)} of {page_count} file {os.path.basename(path)}")
                for image in images:
                    left += 1
                    if left > page_to + 1:
                        break
                    yield np.array(image)
        except (PDFPageCountError, PDFSyntaxError) as error:
            raise BadFileFormatError(f"Bad pdf file:\n file_name = {os.path.basename(path)} \n exception = {error.args}")

    def _convert_to_gray(self, image: ndarray) -> ndarray:
        import cv2
        import numpy as np

        gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        gray_image = self._binarization(gray_image)
        return gray_image

    def _binarization(self, gray_image: ndarray) -> ndarray:
        import numpy as np

        if gray_image.mean() < 220:  # filter black and white image
            binary_mask = gray_image >= np.quantile(gray_image, 0.05)
            gray_image[binary_mask] = 255
        return gray_image
