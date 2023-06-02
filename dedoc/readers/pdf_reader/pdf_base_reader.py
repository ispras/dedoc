import logging
import math
import os
from abc import abstractmethod
from collections import namedtuple
from itertools import chain
from typing import List, Optional, Tuple, Iterator
import cv2
import numpy as np
from joblib import Parallel, delayed
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError

import dedoc.utils.parameter_utils as param_utils
from dedoc.attachments_extractors.concrete_attachments_extractors.pdf_attachments_extractor import PDFAttachmentsExtractor
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_mimes, recognized_extensions
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.metadata_extractor import LineMetadataExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.scan_paragraph_classifier_extractor import ScanParagraphClassifierExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer
from dedoc.readers.pdf_reader.utils.header_footers_analysis import footer_header_analysis
from dedoc.readers.pdf_reader.utils.line_object_linker import LineObjectLinker
from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
from dedoc.utils.pdf_utils import get_page_slice, get_pdf_page_count
from dedoc.utils.utils import flatten
from dedoc.utils.utils import get_file_mime_type, splitext_

ParametersForParseDoc = namedtuple("ParametersForParseDoc", ["orient_analysis_cells",
                                                             "orient_cell_angle",
                                                             "is_one_column_document",
                                                             "document_orientation",
                                                             "document_type",
                                                             "language",
                                                             "need_header_footers_analysis",
                                                             "need_pdf_table_analysis",
                                                             "first_page",
                                                             "last_page",
                                                             "need_binarization",
                                                             'table_type',
                                                             "is_one_column_document_list"])


class PdfBaseReader(BaseReader):
    """
    Base class for pdf documents parsing.
    """
    def __init__(self, config: dict) -> None:
        """
        :param config: configuration of the reader, e.g. logger for logging
        """
        self.table_recognizer = TableRecognizer(config=config)
        self.metadata_extractor = LineMetadataExtractor(config=config)
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self.attachment_extractor = PDFAttachmentsExtractor(config=config)
        self.linker = LineObjectLinker(config=config)
        self.paragraph_extractor = ScanParagraphClassifierExtractor(config=config)

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters
        first_page, last_page = get_page_slice(parameters)
        params_for_parse = ParametersForParseDoc(
            language=param_utils.get_param_language(parameters),
            orient_analysis_cells=param_utils.get_param_orient_analysis_cells(parameters),
            orient_cell_angle=param_utils.get_param_orient_cell_angle(parameters),
            is_one_column_document=param_utils.get_param_is_one_column_document(parameters),
            document_orientation=param_utils.get_param_document_orientation(parameters),
            document_type=document_type,
            need_header_footers_analysis=param_utils.get_param_need_header_footers_analysis(parameters),
            need_pdf_table_analysis=param_utils.get_param_need_pdf_table_analysis(parameters),
            first_page=first_page,
            last_page=last_page,
            need_binarization=param_utils.get_param_need_binarization(parameters),
            table_type=param_utils.get_param_table_type(parameters),
            is_one_column_document_list=param_utils.get_is_one_column_document_list(parameters)
        )

        lines, scan_tables, attachments, warnings, other_fields = self._parse_document(path, params_for_parse)
        tables = []
        for scan_table in scan_tables:
            metadata = TableMetadata(page_id=scan_table.page_number, uid=scan_table.name)
            cells = [[cell for cell in row] for row in scan_table.matrix_cells]
            text_cells = [[cell.text for cell in row] for row in scan_table.matrix_cells]
            table = Table(metadata=metadata, cells=text_cells, cells_properties=cells)
            tables.append(table)

        if self._can_contain_attachements(path) and self.attachment_extractor.with_attachments(parameters):
            tmp_dir = os.path.dirname(path)
            file_name = os.path.basename(path)
            attachments += self.attachment_extractor.get_attachments(tmpdir=tmp_dir, filename=file_name, parameters=parameters)

        result = UnstructuredDocument(lines=lines, tables=tables, attachments=attachments, warnings=warnings, metadata=other_fields)
        return self._postprocess(result)

    def _can_contain_attachements(self, path: str) -> bool:
        can_contain_attachments = False
        mime = get_file_mime_type(path)
        if mime in recognized_mimes.pdf_like_format:
            can_contain_attachments = True
        return can_contain_attachments

    def _parse_document(self, path: str, parameters: ParametersForParseDoc) -> Tuple[List[LineWithMeta],
                                                                                     List[ScanTable],
                                                                                     List[PdfImageAttachment],
                                                                                     List[str],
                                                                                     Optional[dict]]:
        first_page = 0 if parameters.first_page is None else parameters.first_page
        last_page = math.inf if parameters.last_page is None else parameters.last_page
        images = self._get_images(path)

        page_with_images = self._images_slice(images, first_page, last_page)
        result = Parallel(n_jobs=self.config["n_jobs"])(delayed(self._process_one_page_with_flag)(partially_parsed,
                                                                                                  image,
                                                                                                  parameters,
                                                                                                  page_number,
                                                                                                  path)
                                                        for partially_parsed, page_number, image in page_with_images)
        partially_parsed = result[-1][0] if len(result) > 0 else False
        result = [item[1] for item in result]

        if first_page > 0 or partially_parsed:
            warnings = ["The document is partially parsed"]
            metadata = {"first_page": first_page}
            if last_page != math.inf:
                metadata["last_page"] = last_page
        else:
            warnings = []
            metadata = None

        if len(result) == 0:
            all_lines, unref_tables, attachments = [], [], []
        else:
            all_lines, unref_tables, attachments = map(list, map(flatten, zip(*result)))
        if parameters.need_header_footers_analysis:
            lines = [lines for lines, _, _ in result]
            lines, headers, footers = footer_header_analysis(lines)
            all_lines = list(flatten(lines))
        mp_tables = self.table_recognizer.convert_to_multipages_tables(unref_tables, lines_with_meta=all_lines)
        all_lines_with_links = self.linker.link_objects(lines=all_lines, tables=mp_tables, images=attachments)

        prev_line = None
        for line in all_lines_with_links:
            line.metadata.tag_hierarchy_level = DefaultStructureExtractor.get_list_hl_with_regexp(line, prev_line)
            prev_line = line

        all_lines_with_paragraphs = self.paragraph_extractor.extract(all_lines_with_links)
        return all_lines_with_paragraphs, mp_tables, attachments, warnings, metadata

    def _images_slice(self, images: Iterator[np.ndarray],
                      page_from: int,
                      page_to: int) -> Iterator[Tuple[bool, int, Optional[np.ndarray]]]:
        if page_from >= page_to:
            return
        extended_images = chain(images, [None, None])
        page_num = 0
        image = next(extended_images)
        try:
            while image is not None:
                next_image = next(extended_images)
                if page_num + 1 >= page_to:
                    yield next_image is not None, page_num, image
                    break
                if page_num >= page_from:
                    yield False, page_num, image
                page_num += 1
                image = next_image
        except StopIteration:
            yield False, page_num, image

    def _process_one_page_with_flag(self,
                                    partially_parsed: bool,
                                    image: np.ndarray,
                                    parameters: ParametersForParseDoc,
                                    page_number: int,
                                    path: str) \
            -> Tuple[bool, Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment]]]:
        return partially_parsed, self._process_one_page(image, parameters, page_number, path)

    @abstractmethod
    def _process_one_page(self, image: np.ndarray, parameters: ParametersForParseDoc, page_number: int, path: str) \
            -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment]]:
        pass

    def _get_images(self, path: str) -> Iterator[np.ndarray]:
        mime = get_file_mime_type(path)
        if mime in recognized_mimes.pdf_like_format:
            yield from self._split_pdf2image(path)
        elif mime in recognized_mimes.image_like_format or path.endswith(tuple(recognized_extensions.image_like_format)):
            image = cv2.imread(path)
            if image is None:
                raise BadFileFormatException("seems file {} not an image".format(os.path.basename(path)))
            yield image
        else:
            raise BadFileFormatException("Unsupported input format: {}".format(splitext_(path)[1]))  # noqa

    def _split_pdf2image(self, path: str) -> Iterator[np.ndarray]:
        try:
            page_count = get_pdf_page_count(path)
            file_name = os.path.basename(path)
            step = max(self.config["n_jobs"], 3)
            left = 1
            images = None
            while images is None or len(images) > 0:
                right = left + step - 1
                images = convert_from_path(path, first_page=left, last_page=right)  # noqa
                self.logger.info("get page from {} to {} of {} file {}".format(left, right, page_count, file_name))
                left += step
                for image in images:
                    yield np.array(image)
        except (PDFPageCountError, PDFSyntaxError) as error:
            raise BadFileFormatException("Bad pdf file:\n file_name = {} \n exception = {}".format(
                os.path.basename(path), error.args
            ))

    def _convert_to_gray(self, image: np.ndarray) -> np.ndarray:
        gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        gray_image = self._binarization(gray_image)
        return gray_image

    def _binarization(self, gray_image: np.ndarray) -> np.ndarray:
        if gray_image.mean() < 220:  # filter black and white image
            binary_mask = gray_image >= np.quantile(gray_image, 0.05)
            gray_image[binary_mask] = 255
        return gray_image

    def eval_tables_by_batch(self,
                             batch: Iterator[np.ndarray],
                             page_number_begin: int,
                             language: str,
                             orient_analysis_cells: bool = False,
                             orient_cell_angle: int = 270,
                             table_type: str = "") -> Tuple[List[np.ndarray], List[ScanTable]]:

        result_batch = Parallel(n_jobs=self.config["n_jobs"])(
            delayed(self.table_recognizer.recognize_tables_from_image)(
                image, page_number_begin + i, language, orient_analysis_cells, orient_cell_angle, table_type)
            for i, image in enumerate(batch))  # noqa
        return result_batch
