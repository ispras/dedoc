import os.path
from typing import List, Optional, Tuple

from dedocutils.data_structures import BBox
from numpy import ndarray

from dedoc.common.exceptions.java_not_found_error import JavaNotFoundError
from dedoc.common.exceptions.tabby_pdf_error import TabbyPdfError
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_base_reader import ParametersForParseDoc, PdfBaseReader


class PdfTabbyReader(PdfBaseReader):
    """
    This class allows to extract content (textual and table) from the .pdf documents with a textual layer (copyable documents).
    It uses java code to get the result.

    It is recommended to use this class as a handler for PDF documents with a correct textual layer
    if you don't need to check textual layer correctness.
    For more information, look to `pdf_with_text_layer` option description in :ref:`pdf_handling_parameters`.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        import os
        from dedoc.extensions import recognized_extensions, recognized_mimes
        from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.onepage_table_extractor import \
            OnePageTableExtractor
        from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.table_attribute_extractor import \
            TableHeaderExtractor

        super().__init__(config=config, recognized_extensions=recognized_extensions.pdf_like_format, recognized_mimes=recognized_mimes.pdf_like_format)
        self.tabby_java_version = "2.0.0"
        self.jar_name = "ispras_tbl_extr.jar"
        self.jar_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tabbypdf", "jars"))
        self.java_not_found_error = "`java` command is not found from this Python process. Please ensure Java is installed and PATH is set for `java`"
        self.default_config = {"JAR_PATH": os.path.join(self.jar_dir, self.jar_name)}
        self.table_header_selector = TableHeaderExtractor(logger=self.logger)
        self.table_extractor = OnePageTableExtractor(config=config, logger=self.logger)

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader (PDF format is supported only).
        This method returns `True` only when the key `pdf_with_text_layer` with value `tabby` is set in the dictionary `parameters`.

        You can look to :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer
        return super().can_read(file_path=file_path, mime=mime, extension=extension) and get_param_pdf_with_txt_layer(parameters) == "tabby"

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.

        You can also see :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.
        """
        import tempfile
        from dedoc.utils.parameter_utils import get_param_with_attachments
        parameters = {} if parameters is None else parameters
        warnings = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            lines, tables, attachments, document_metadata = self.__extract(path=file_path, parameters=parameters, warnings=warnings, tmp_dir=tmp_dir)

        if get_param_with_attachments(parameters) and self.attachment_extractor.can_extract(file_path):
            attachments += self.attachment_extractor.extract(file_path=file_path, parameters=parameters)

        lines = [line for line_group in lines for line in line_group.split("\n")]
        lines = self.paragraph_extractor.extract(lines)
        result = UnstructuredDocument(lines=lines, tables=tables, attachments=attachments, warnings=warnings, metadata=document_metadata)

        return self._postprocess(result)

    def __extract(self, path: str, parameters: dict, warnings: List[str], tmp_dir: str)\
            -> Tuple[List[LineWithMeta], List[Table], List[PdfImageAttachment], Optional[dict]]:
        import math
        from dedoc.utils.pdf_utils import get_pdf_page_count
        from dedoc.utils.utils import calculate_file_hash
        from dedoc.utils.parameter_utils import get_param_page_slice, get_param_with_attachments
        from dedoc.utils.parameter_utils import get_param_need_gost_frame_analysis

        all_lines, all_tables, all_scan_tables, all_attached_images = [], [], [], []
        with_attachments = get_param_with_attachments(parameters)
        document_metadata = None

        file_hash = calculate_file_hash(path=path)
        page_count = get_pdf_page_count(path)
        page_count = math.inf if page_count is None else page_count
        first_page, last_page = get_param_page_slice(parameters)

        empty_page_limit = (first_page is not None and first_page >= page_count) or (last_page is not None and first_page >= last_page)
        partial_page_limit = (first_page is not None and first_page > 0) or (last_page is not None and last_page < page_count)
        if empty_page_limit or partial_page_limit:
            warnings.append("The document is partially parsed")
            document_metadata = dict(first_page=first_page)
            if last_page is not None:
                document_metadata["last_page"] = last_page

            if empty_page_limit:
                return all_lines, all_tables, all_attached_images, document_metadata

        remove_gost_frame = get_param_need_gost_frame_analysis(parameters)
        gost_json_path = self.__save_gost_frame_boxes_to_json(first_page=first_page, last_page=last_page, page_count=page_count, tmp_dir=tmp_dir, path=path) \
            if remove_gost_frame else ""

        # in java tabby reader page numeration starts with 1, end_page is included
        first_tabby_page = first_page + 1 if first_page is not None else 1
        last_tabby_page = page_count if (last_page is None) or (last_page is not None and last_page > page_count) else last_page
        self.logger.info(f"Reading PDF pages from {first_tabby_page} to {last_tabby_page}")
        document = self.__process_pdf(path=path,
                                      start_page=first_tabby_page,
                                      end_page=last_tabby_page,
                                      tmp_dir=tmp_dir,
                                      gost_json_path=gost_json_path,
                                      remove_frame=remove_gost_frame)

        pages = document.get("pages", [])
        for page in pages:
            page_lines = self.__get_lines_with_location(page, file_hash)
            if page_lines:
                all_lines.extend(page_lines)
            scan_tables = self.__get_tables(page)
            all_scan_tables.extend(scan_tables)

            attached_images = self.__get_attached_images(page=page, parameters=parameters, path=path) if with_attachments else []
            if attached_images:
                all_attached_images.extend(attached_images)

        mp_tables = self.table_recognizer.convert_to_multipages_tables(all_scan_tables, lines_with_meta=all_lines)
        all_lines = self.linker.link_objects(lines=all_lines, tables=mp_tables, images=all_attached_images)

        return all_lines, mp_tables, all_attached_images, document_metadata

    def __save_gost_frame_boxes_to_json(self, first_page: Optional[int], last_page: Optional[int], page_count: int, path: str, tmp_dir: str) -> str:
        from joblib import Parallel, delayed
        import json

        first_page = 0 if first_page is None or first_page < 0 else first_page
        last_page = page_count if (last_page is None) or (last_page is not None and last_page > page_count) else last_page
        images = self._get_images(path, first_page, last_page)

        gost_analyzed_images = Parallel(n_jobs=self.config["n_jobs"])(delayed(self.gost_frame_recognizer.rec_and_clean_frame)(image) for image in images)

        result_dict = {
            page_number: {**page_data[1].to_dict(), **{"original_image_width": page_data[2][1], "original_image_height": page_data[2][0]}}
            for page_number, page_data in enumerate(gost_analyzed_images, start=first_page)
        }

        result_json_path = os.path.join(tmp_dir, "gost_frame_bboxes.json")
        with open(result_json_path, "w") as f:
            json.dump(result_dict, f)

        return result_json_path

    def __get_tables(self, page: dict) -> List[ScanTable]:
        from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
        from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
        from dedoc.data_structures.line_metadata import LineMetadata

        scan_tables = []
        page_number = page["number"]
        page_width = int(page["width"])
        page_height = int(page["height"])

        for table in page["tables"]:
            table_bbox = BBox(x_top_left=table["x_top_left"], y_top_left=table["y_top_left"], width=table["width"], height=table["height"])
            order = table["order"]
            rows = table["rows"]
            cell_properties = table["cell_properties"]
            assert len(rows) == len(cell_properties)

            cells = []
            for num_row, row in enumerate(rows):
                assert len(row) == len(cell_properties[num_row])

                result_row = []
                for num_col, cell in enumerate(row):
                    annotations = []
                    cell_blocks = cell["cell_blocks"]

                    for c in cell_blocks:
                        cell_bbox = BBox(x_top_left=int(c["x_top_left"]), y_top_left=int(c["y_top_left"]), width=int(c["width"]), height=int(c["height"]))
                        annotations.append(BBoxAnnotation(c["start"], c["end"], cell_bbox, page_width=page_width, page_height=page_height))

                    current_cell_properties = cell_properties[num_row][num_col]
                    bbox = BBox(x_top_left=int(current_cell_properties["x_top_left"]),
                                y_top_left=int(current_cell_properties["y_top_left"]),
                                width=int(current_cell_properties["width"]),
                                height=int(current_cell_properties["height"]))

                    result_row.append(Cell(
                        bbox=bbox,
                        lines=[LineWithMeta(line=cell["text"], metadata=LineMetadata(page_id=page_number, line_id=0), annotations=annotations)],
                        colspan=current_cell_properties["col_span"],
                        rowspan=current_cell_properties["row_span"],
                        invisible=bool(current_cell_properties["invisible"])
                    ))
                cells.append(result_row)

            try:
                cells = self.table_extractor.handle_cells(cells)
                scan_tables.append(ScanTable(page_number=page_number, cells=cells, bbox=table_bbox, order=order))
            except Exception as ex:
                self.logger.warning(f"Warning: unrecognized table on page {self.page_number}. {ex}")
                if self.config.get("debug_mode", False):
                    raise ex

        return scan_tables

    def __get_attached_images(self, page: dict, parameters: dict, path: str) -> List[PdfImageAttachment]:
        import os
        import shutil
        import uuid
        from dedoc.readers.pdf_reader.data_classes.tables.location import Location
        from dedoc.utils.utils import get_unique_name
        from dedoc.utils.parameter_utils import get_param_attachments_dir, get_param_need_content_analysis

        attachments_dir = get_param_attachments_dir(parameters, path)
        need_content_analysis = get_param_need_content_analysis(parameters)

        image_attachment_list = []
        for image_dict in page["images"]:
            image_location = Location(
                page_number=page["number"],
                bbox=BBox(x_top_left=image_dict["x_top_left"], y_top_left=image_dict["y_top_left"], width=image_dict["width"], height=image_dict["height"])
            )

            tmp_file_name = get_unique_name(image_dict["original_name"])
            tmp_file_path = os.path.join(attachments_dir, tmp_file_name)
            shutil.move(image_dict["tmp_file_path"], tmp_file_path)

            image_attachment = PdfImageAttachment(
                original_name=image_dict["original_name"],
                tmp_file_path=tmp_file_path,
                need_content_analysis=need_content_analysis,
                uid=f"attach_{uuid.uuid4()}",
                location=image_location
            )
            image_attachment_list.append(image_attachment)

        return image_attachment_list

    def __get_lines_with_location(self, page: dict, file_hash: str) -> List[LineWithLocation]:
        from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
        from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
        from dedoc.data_structures.concrete_annotations.indentation_annotation import IndentationAnnotation
        from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
        from dedoc.data_structures.concrete_annotations.linked_text_annotation import LinkedTextAnnotation
        from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
        from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
        from dedoc.data_structures.concrete_annotations.style_annotation import StyleAnnotation
        from dedoc.data_structures.line_metadata import LineMetadata
        from dedoc.readers.pdf_reader.data_classes.tables.location import Location

        lines = []
        page_number, page_width, page_height = page["number"], int(page["width"]), int(page["height"])
        labeling_mode = self.config.get("labeling_mode", False)

        for block in page["blocks"]:
            annotations = []
            order = block["order"]
            block_text = block["text"]
            len_block = len(block_text)
            annotations.append(IndentationAnnotation(0, len_block, str(block["indent"])))
            annotations.append(SpacingAnnotation(0, len_block, str(block["spacing"])))

            for annotation in block["annotations"]:
                start = annotation["start"]
                end = annotation["end"]

                if not labeling_mode:
                    box = BBox(x_top_left=int(annotation["x_top_left"]), y_top_left=int(annotation["y_top_left"]),
                               width=int(annotation["width"]), height=int(annotation["height"]))
                    annotations.append(BBoxAnnotation(start, end, box, page_width=page_width, page_height=page_height))

                annotations.append(SizeAnnotation(start, end, str(annotation["font_size"])))
                annotations.append(StyleAnnotation(start, end, annotation["font_name"]))

                if annotation["is_bold"]:
                    annotations.append(BoldAnnotation(start, end, "True"))

                if annotation["is_italic"]:
                    annotations.append(ItalicAnnotation(start, end, "True"))

                if annotation["metadata"] == "LINK":
                    annotations.append(LinkedTextAnnotation(start, end, annotation["url"]))

            bbox = BBox(x_top_left=int(block["x_top_left"]), y_top_left=int(block["y_top_left"]), width=int(block["width"]), height=int(block["height"]))
            if labeling_mode:
                annotations.append(BBoxAnnotation(0, len_block, bbox, page_width=page_width, page_height=page_height))

            meta = block["metadata"].lower()
            uid = f"txt_{file_hash}_{order}"

            metadata = LineMetadata(page_id=page_number, line_id=order)
            line_with_location = LineWithLocation(line=block_text,
                                                  metadata=metadata,
                                                  annotations=annotations,
                                                  uid=uid,
                                                  location=Location(bbox=bbox, page_number=page_number),
                                                  order=order)
            line_with_location.metadata.tag_hierarchy_level = self.__get_tag(line_with_location, meta)

            lines.append(line_with_location)

        return lines

    def __get_tag(self, line: LineWithMeta, line_type: str) -> HierarchyLevel:
        from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_dotted_item_depth

        if line_type == HierarchyLevel.header:
            header_level = get_dotted_item_depth(line.line)
            header_level = header_level if header_level != -1 else 1
            return HierarchyLevel(1, header_level, False, line_type)

        if line_type == "litem":  # TODO automatic list depth and merge list items from multiple lines
            return HierarchyLevel(None, None, False, HierarchyLevel.list_item)

        return HierarchyLevel.create_unknown()

    def __jar_path(self) -> str:
        import os
        return os.environ.get("TABBY_JAR", self.default_config["JAR_PATH"])

    def __run(self,
              path: str,
              tmp_dir: str,
              encoding: str = "utf-8",
              start_page: int = None,
              end_page: int = None,
              remove_frame: bool = False,
              gost_json_path: str = ""
              ) -> bytes:
        import subprocess

        args = ["java"] + ["-jar", self.__jar_path(), "-i", path, "-tmp", f"{tmp_dir}/"]
        if remove_frame:
            args += ["-rf", gost_json_path]
        if start_page is not None and end_page is not None:
            args += ["-sp", str(start_page), "-ep", str(end_page)]
        try:
            result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, check=True)
            if result.stderr:
                self.logger.warning(f"Got stderr: {result.stderr.decode(encoding)}")
            return result.stdout
        except FileNotFoundError:
            raise JavaNotFoundError(self.java_not_found_error)
        except subprocess.CalledProcessError as e:
            raise TabbyPdfError(e.stderr.decode(encoding))

    def __process_pdf(self,
                      path: str,
                      tmp_dir: str,
                      start_page: int = None,
                      end_page: int = None,
                      gost_json_path: str = "",
                      remove_frame: bool = False) -> dict:
        import json
        import os

        self.__run(path=path, start_page=start_page, end_page=end_page, tmp_dir=tmp_dir, remove_frame=remove_frame, gost_json_path=gost_json_path)

        with open(os.path.join(tmp_dir, "data.json"), "r") as response:
            document = json.load(response)

        return document

    def _process_one_page(self,
                          image: ndarray,
                          parameters: ParametersForParseDoc,
                          page_number: int,
                          path: str) -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment], List[float]]:

        return [], [], [], []
