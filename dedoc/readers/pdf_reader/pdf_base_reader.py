from abc import abstractmethod
from collections import namedtuple
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

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
    "pdf_with_txt_layer",
    "extract_notes"
])


class PdfBaseReader(BaseReader):
    """
    Base class for pdf documents parsing.
    """

    def __init__(self, *, config: Optional[dict] = None, recognized_extensions: Optional[Set[str]] = None, recognized_mimes: Optional[Set[str]] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions, recognized_mimes=recognized_mimes)

        from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.metadata_extractor import LineMetadataExtractor
        from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer
        from dedoc.attachments_extractors.concrete_attachments_extractors.pdf_attachments_extractor import PDFAttachmentsExtractor

        self.config["n_jobs"] = self.config.get("n_jobs", 1)
        self.table_recognizer = TableRecognizer(config=self.config)
        self.metadata_extractor = LineMetadataExtractor(config=self.config)
        self.attachment_extractor = PDFAttachmentsExtractor(config=self.config)
        # The linker / paragraph classifier / header-footer / notes / GOST components run only in the main-process
        # post-read assembly; the per-page staged-pipeline workers never touch them. Build them lazily so a worker's
        # reader does not import the paragraph classifier's pandas + sklearn feature chain (~130 MB per worker) it never
        # uses. Each is exposed as a property that builds (and imports) on first access. See TENSORRT_INT8.md.
        self._linker = None
        self._paragraph_extractor = None
        self._gost_frame_recognizer = None
        self._header_footer_detector = None
        self._notes_extractor = None

    @property
    def linker(self):  # noqa
        if self._linker is None:
            from dedoc.readers.pdf_reader.utils.line_object_linker import LineObjectLinker
            self._linker = LineObjectLinker(config=self.config)
        return self._linker

    @property
    def paragraph_extractor(self):  # noqa
        if self._paragraph_extractor is None:
            from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.scan_paragraph_classifier_extractor import ScanParagraphClassifierExtractor
            self._paragraph_extractor = ScanParagraphClassifierExtractor(config=self.config)
        return self._paragraph_extractor

    @property
    def gost_frame_recognizer(self):  # noqa
        if self._gost_frame_recognizer is None:
            from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.gost_frame_recognizer import GOSTFrameRecognizer
            self._gost_frame_recognizer = GOSTFrameRecognizer(config=self.config)
        return self._gost_frame_recognizer

    @property
    def header_footer_detector(self):  # noqa
        if self._header_footer_detector is None:
            from dedoc.readers.pdf_reader.utils.header_footers_analysis import HeaderFooterDetector
            self._header_footer_detector = HeaderFooterDetector()
        return self._header_footer_detector

    @property
    def notes_extractor(self):  # noqa
        if self._notes_extractor is None:
            from dedoc.readers.pdf_reader.utils.notes_extractor import PdfNotesExtractor
            self._notes_extractor = PdfNotesExtractor(logger=self.logger)
        return self._notes_extractor

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
            pdf_with_txt_layer=param_utils.get_param_pdf_with_txt_layer(parameters),
            extract_notes=param_utils.get_bool_parameter(parameters, "extract_notes"),
        )

        lines, scan_tables, attachments, warnings, metadata = self._parse_document(file_path, params_for_parse)

        if params_for_parse.with_attachments and self.attachment_extractor.can_extract(file_path):
            attachments += self.attachment_extractor.extract(file_path=file_path, parameters=parameters)

        result = UnstructuredDocument(lines=lines, tables=scan_tables, attachments=attachments, warnings=warnings, metadata=metadata)
        return self._postprocess(result)

    def _parse_document(self, path: str, parameters: ParametersForParseDoc) \
            -> Tuple[List[LineWithMeta], List[ScanTable], List[PdfImageAttachment], List[str], Optional[dict]]:
        import math
        from joblib import Parallel, delayed
        from dedoc.data_structures.hierarchy_level import HierarchyLevel
        from dedoc.utils.pdf_utils import get_pdf_page_count
        from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
        from dedoc.utils.utils import flatten

        first_page = 0 if parameters.first_page is None or parameters.first_page < 0 else parameters.first_page
        last_page = math.inf if parameters.last_page is None else parameters.last_page
        images = self._get_images(path, first_page, last_page)

        orchestrator_warnings = []
        if parameters.need_gost_frame_analysis and isinstance(self, (PdfImageReader, PdfTxtlayerReader)):
            result, gost_analyzed_images = self._process_document_with_gost_frame(images=images, first_page=first_page, parameters=parameters, path=path)
        elif self.config.get("use_stage_pipeline", False) and isinstance(self, PdfImageReader):
            result, orchestrator_warnings = self._process_pages_via_stages(parameters=parameters, path=path, first_page=first_page, last_page=last_page)
        elif self.config.get("use_orchestrator", False):
            result, orchestrator_warnings = self._process_pages_orchestrated(images=images, parameters=parameters, path=path, first_page=first_page)
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
        warnings.extend(orchestrator_warnings)

        if len(result) == 0:
            all_lines, unref_tables, attachments, page_angles = [], [], [], []
        else:
            all_lines, unref_tables, attachments, page_angles = map(list, map(flatten, zip(*result)))

        if parameters.need_header_footers_analysis:
            lines = [lines for lines, _, _, _ in result]
            lines, headers, footers = self.header_footer_detector.detect(lines)
            all_lines = list(flatten(lines))

        if parameters.need_gost_frame_analysis and isinstance(self, PdfImageReader):
            self._shift_all_contents(lines=all_lines, onepage_tables=unref_tables, attachments=attachments, gost_analyzed_images=gost_analyzed_images)

        mp_tables = self.table_recognizer.convert_to_multipages_tables(unref_tables, lines_with_meta=all_lines)
        all_lines_with_links = self.linker.link_objects(lines=all_lines, tables=mp_tables, images=attachments)

        for line in all_lines_with_links:
            line.metadata.tag_hierarchy_level = HierarchyLevel.create_unknown()

        all_lines_with_paragraphs = self.paragraph_extractor.extract(all_lines_with_links)
        if page_angles:
            metadata["rotated_page_angles"] = page_angles

        if parameters.extract_notes:
            self.notes_extractor.extract(path, all_lines_with_links + self._get_table_lines(mp_tables))

        return all_lines_with_paragraphs, mp_tables, attachments, warnings, metadata

    def _get_table_lines(self, tables: List[ScanTable]) -> List[LineWithMeta]:
        from itertools import chain

        table_lines = []
        for table in tables:
            table_lines.extend(chain.from_iterable([cell.lines for row in table.cells for cell in row]))
        return table_lines

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

    def _shift_all_contents(self, lines: List[LineWithMeta], onepage_tables: List[ScanTable], attachments: List[PdfImageAttachment],
                            gost_analyzed_images: Dict[int, Tuple[ndarray, BBox, Tuple[int, ...]]]) -> None:
        """
            Shift all recognized content relative to the original source image
        """
        # shift unref_tables
        for scan_table in onepage_tables:
            for location in scan_table.locations:
                page_number = location.page_number
                location.shift(shift_x=gost_analyzed_images[page_number][1].x_top_left, shift_y=gost_analyzed_images[page_number][1].y_top_left)
                location.page_width, location.page_height = gost_analyzed_images[page_number][2][1], gost_analyzed_images[page_number][2][0]

            page_number = scan_table.locations[0].page_number
            for row in scan_table.cells:
                for cell in row:
                    orig_image_width, orig_image_height = gost_analyzed_images[page_number][2][1], gost_analyzed_images[page_number][2][0]
                    gost_frame_bbox = gost_analyzed_images[page_number][1]
                    shift_x, shift_y = gost_frame_bbox.x_top_left, gost_frame_bbox.y_top_left
                    cell.shift(shift_x=shift_x, shift_y=shift_y, image_width=orig_image_width, image_height=orig_image_height)

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

    def _process_pages_orchestrated(self, images: Iterator[ndarray], parameters: ParametersForParseDoc, path: str, first_page: int) \
            -> Tuple[List[Tuple], List[str]]:
        """
        Run per-page processing through the staged Orchestrator (thread pool, one shared model copy)
        instead of joblib. Enabled via ``config["use_orchestrator"]``; the number of CPU workers is taken
        from ``config["cpu_workers"]`` (falls back to ``n_jobs``). A page that fails becomes an empty
        result plus a warning, so the rest of the document is still parsed.
        """
        from dedoc.pipeline import Orchestrator, Resource, Stage

        # warm up the lazily-loaded orientation model once, before threads start, to avoid an init race
        needs_classifier = parameters.is_one_column_document is None or parameters.document_orientation is None
        if needs_classifier and hasattr(self, "column_orientation_classifier"):
            _ = self.column_orientation_classifier.net

        def process_page(payload: Tuple[int, ndarray], ctx: object) -> Tuple:
            page_number, image = payload
            return self._process_one_page(image, parameters, page_number, path)

        cpu_workers = int(self.config.get("cpu_workers", self.config.get("n_jobs", 1)))
        orchestrator = Orchestrator(cpu_workers=cpu_workers, logger=self.logger)
        pages = ((page_number, image) for page_number, image in enumerate(images, start=first_page))
        state = orchestrator.run(pages=pages, page_stages=[Stage("process_page", process_page, resource=Resource.CPU)])
        result = [page if page is not None else ([], [], [], []) for page in state.pages]
        return result, state.warnings

    def _get_stage_executor(self, pool_sizes: Dict[str, int]) -> Any:
        """
        Build the staged executor once and reuse it across documents, so persistent process workers keep
        their loaded models warm (only rebuilt if the process/worker configuration changes).
        """
        import dedoc.pipeline.pdf_stages as pdf_stages
        from dedoc.pipeline.executor import LocalExecutor, ProcessExecutor

        use_processes = self.config.get("stage_pipeline_processes", False)
        key = (use_processes, tuple(sorted(pool_sizes.items())))
        if getattr(self, "_stage_executor_key", None) == key:
            return self._stage_executor

        old_executor = getattr(self, "_stage_executor", None)
        if old_executor is not None:
            old_executor.shutdown()

        if use_processes:
            on_gpu = bool(self.config.get("on_gpu", False))
            ocr_engine = self.config.get("ocr_engine", "tesseract")  # pass the selected OCR engine into worker readers
            # forward the worker-relevant OCR knobs so a config override reaches the worker readers (their defaults
            # live in the code, so only explicitly-set overrides need to be passed through the process boundary)
            fwd = {k: self.config[k] for k in ("hybrid_reading_order", "hybrid_det_max_side", "hybrid_homoglyph_fix", "table_hough_scale", "hybrid_rec_engine") if k in self.config}
            # only the single GPU worker gets a CUDA reader; CPU workers stay on CPU (no per-worker CUDA context)
            executor = ProcessExecutor(pool_sizes=pool_sizes, setup_fn=pdf_stages.setup, setup_arg={"on_gpu": False, "ocr_engine": ocr_engine, **fwd},
                                       gpu_setup_fn=pdf_stages.setup, gpu_setup_arg={"on_gpu": on_gpu, "ocr_engine": ocr_engine, **fwd})
        else:
            pdf_stages._READER = self  # reuse this reader in-process
            executor = LocalExecutor(pool_sizes)
        self._stage_executor = executor
        self._stage_executor_key = key
        return executor

    def _process_pages_via_stages(self, parameters: ParametersForParseDoc, path: str, first_page: int, last_page: float) \
            -> Tuple[List[Tuple], List[str]]:
        """
        Phase 2c: run the per-page work as a decomposed task graph (see ARCHITECTURE.md §9) via the staged
        Scheduler. A page *document* dict flows through render/binarize/orient_predict/deskew/layout/ocr/table,
        each stage augmenting it; per-page results are reassembled into the ``_process_one_page`` tuple shape
        so the document-level barriers below run unchanged. Enabled via ``config["use_stage_pipeline"]``;
        ``config["stage_pipeline_processes"]`` switches to real process workers.

        Rendering is lazy: the ``render`` stage rasterizes each page on demand, and the scheduler keeps at most
        ``config["max_inflight_pages"]`` pages in flight, so peak memory is bounded by the worker count rather
        than the document size.
        """
        import math
        import dedoc.pipeline.pdf_stages as pdf_stages
        from dedoc.pipeline.scheduler import Scheduler
        from dedoc.utils.pdf_utils import get_pdf_page_count

        page_count = get_pdf_page_count(path) or 1
        end = page_count if last_page == math.inf else min(int(last_page), page_count)
        pages = list(range(first_page, end))
        specs = pdf_stages.build_specs(parameters, ocr_engine=self.config.get("ocr_engine", "tesseract"))
        workers = int(self.config.get("cpu_workers", 4))
        pool_sizes = {"cpu_process": workers, "thread": workers, "gpu": int(self.config.get("gpu_workers", 1))}
        max_inflight = int(self.config.get("max_inflight_pages", max(4, 2 * workers)))

        def seed(page: int) -> dict:
            return {"page_number": page, "params": parameters, "path": path}  # the render stage produces the image

        if not self.config.get("stage_pipeline_processes", False) and any(spec.name == "orient_predict" for spec in specs):
            _ = self.column_orientation_classifier.net  # warm the lazily-loaded model before threads start

        executor = self._get_stage_executor(pool_sizes)  # persistent across documents (workers keep models warm)

        from dedoc.pipeline.shared_image import ShmRef

        release = getattr(executor, "release_output", None)

        def drop_image(output: dict) -> dict:
            # free large arrays in place; if they live in shared buffers, hand those buffers back to the executor pool
            for key in [k for k, v in output.items() if isinstance(v, ShmRef)]:
                if release is not None:
                    release(output[key].name)
                output.pop(key)
            return output

        # free each page image once its stages have consumed it, so images do not accumulate over a large document
        doc_result = Scheduler(executor=executor, gpu_batch_timeout=0.05, max_inflight_pages=max_inflight,
                               logger=self.logger).run(specs, pages, seed, reduce_output=drop_image)

        def field(name: str, page: int, key: str, default: Any) -> Any:
            task = doc_result.by_id.get(f"{name}@p{page}")
            return default if task is None or task.output is None else task.output.get(key, default)

        result = []
        for page in pages:
            attachments = list(field("layout", page, "attachments", [])) + list(field("ocr", page, "page_attachments", []))
            # tables flow through to the ocr stage output (and the hybrid split assembles them there, deferred off the
            # table stage); fall back to the table stage for robustness if the ocr stage produced no output.
            ocr_tables = field("ocr", page, "tables", None)
            tables = ocr_tables if ocr_tables is not None else field("table", page, "tables", [])
            result.append((field("ocr", page, "lines", []), tables, attachments, [field("deskew", page, "rotated_angle", 0.0)]))
        return result, doc_result.warnings

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

        import cv2
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
                    image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
                    yield image
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
