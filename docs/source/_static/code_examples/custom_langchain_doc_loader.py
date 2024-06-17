from abc import ABC, abstractmethod
from typing import Dict, Generator, Iterator, List, Optional

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from dedoc.data_structures import TreeNode


class BaseDedocParser(ABC):
    @abstractmethod
    def lazy_parse(self,  # noqa: FOL005
                   obj: str,
                   parsing_parameters: Optional[Dict[str, str]] = None,
                   split: Optional[str] = "document"
                   ) -> Iterator[Document]:
        pass

    def parse(self,  # noqa: FOL005
              obj: str,
              parsing_parameters: Optional[Dict[str, str]] = None,
              split: Optional[str] = "document"
              ) -> List[Document]:
        return list(self.lazy_parse(obj, parsing_parameters, split))


class DedocParser(BaseDedocParser):
    def __init__(self,  # noqa: FOL005
                 manager_config: Optional[dict] = None,
                 ) -> None:
        self.manager_config = manager_config
        from dedoc import DedocManager
        self.dedoc_manager = DedocManager(manager_config=self.manager_config)

    def parse_subparagraphs(self,  # noqa: FOL005
                            doc_tree: TreeNode,
                            doc_metadata: dict
                            ) -> Generator:
        if len(doc_tree.subparagraphs) > 0:
            for subparagraph in doc_tree.subparagraphs:
                yield from self.parse_subparagraphs(doc_tree=subparagraph, doc_metadata=doc_metadata)
        else:
            yield Document(page_content=doc_tree.text, metadata={**doc_metadata, **vars(doc_tree.metadata)})

    def lazy_parse(self,  # noqa: FOL005
                   obj: str,
                   parsing_parameters: Optional[Dict[str, str]] = None,
                   split: Optional[str] = "document"
                   ) -> Iterator[Document]:
        from dedoc.api.api_utils import json2txt

        document_tree = self.dedoc_manager.parse(obj, parameters=parsing_parameters)
        if split == "document":
            text = json2txt(paragraph=document_tree.content.structure)
            yield Document(page_content=text, metadata=vars(document_tree.metadata))
        elif split == "page":
            initial_page_id = document_tree.content.structure.subparagraphs[0].metadata.page_id
            initial_page_text = ""
            initial_page_metadata = vars(document_tree.metadata)
            for node_index, node in enumerate(document_tree.content.structure.subparagraphs):
                if node.metadata.page_id == initial_page_id:
                    initial_page_text += json2txt(node)
                    initial_page_metadata["page_id"] = initial_page_id
                    if node_index == len(document_tree.content.structure.subparagraphs) - 1:
                        yield Document(page_content=initial_page_text, metadata=dict(initial_page_metadata))
                else:
                    yield Document(page_content=initial_page_text, metadata=dict(initial_page_metadata))
                    initial_page_id = node.metadata.page_id
                    initial_page_text = json2txt(node)
                    initial_page_metadata["page_id"] = initial_page_id
        elif split == "line":
            initial_document_metadata = vars(document_tree.metadata)
            for node in document_tree.content.structure.subparagraphs:
                line_metadata = node.metadata
                yield Document(page_content=json2txt(node), metadata={**initial_document_metadata, **vars(line_metadata)})
        elif split == "node":
            yield from self.parse_subparagraphs(doc_tree=document_tree.content.structure, doc_metadata=vars(document_tree.metadata))


class DedocLoader(BaseLoader):
    def __init__(  # noqa: FOL005
        self,
        file_path: str,
        *,
        parsing_params: Optional[dict] = None,
        split: Optional[str] = "document"
    ) -> None:
        """Initialize with file path

        Args:
            parsing_params: Parameters used for document parsing via dedoc. More info available at the link:
                            https://dedoc.readthedocs.io/en/latest/parameters/parameters.html
            split: Controls how the document is divided when being processed
                "document": In this mode, the entire text of the document is returned at once
                "line": In this mode, all text lines of the document are returned one by one
                "page": In this mode, the contents of the document pages are returned one by one
                "node": In this mode, the text contents of the document tree nodes are returned one by one
                        More info available at: https://dedoc.readthedocs.io/en/latest/structure_types/other.html
        """
        self.file_path = file_path
        self.split = split
        self.parsing_params = {**parsing_params, **{"structure_type": "tree" if self.split == "node" else "linear"}}
        self.parser = DedocParser(
            manager_config=self.make_manager_config(),
        )

    def make_manager_config(self) -> dict:  # noqa: C901
        try:
            from dedoc.extensions import recognized_extensions, converted_extensions
            from dedoc.utils.utils import get_mime_extension
            from dedoc.common.exceptions.bad_file_error import BadFileFormatError
        except ImportError:
            raise ImportError(
                "`dedoc` package not found, please install it with "
                "`pip install dedoc`"
                "More info: `https://dedoc.readthedocs.io/en/latest/getting_started/installation.html`"
            )

        mime, extension = get_mime_extension(file_path=self.file_path)

        supported_extensions = {}

        for format_group in recognized_extensions._asdict().keys():
            supported_extensions[format_group] = {*recognized_extensions._asdict()[format_group], *converted_extensions._asdict()[format_group]}

        if extension in supported_extensions["excel_like_format"]:
            from dedoc.converters import ExcelConverter
            from dedoc.readers import ExcelReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = ExcelConverter(), ExcelReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["docx_like_format"]:
            from dedoc.converters import DocxConverter
            from dedoc.readers import DocxReader
            from dedoc.metadata_extractors import DocxMetadataExtractor
            converter, reader, metadata_extractor = DocxConverter(), DocxReader(), DocxMetadataExtractor()
        elif extension in supported_extensions["pptx_like_format"]:
            from dedoc.converters import PptxConverter
            from dedoc.readers import PptxReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = PptxConverter(), PptxReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["html_like_format"]:
            from dedoc.readers import HtmlReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = None, HtmlReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["eml_like_format"]:
            from dedoc.readers import EmailReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = None, EmailReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["mhtml_like_format"]:
            from dedoc.readers import MhtmlReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = None, MhtmlReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["archive_like_format"]:
            from dedoc.readers import ArchiveReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = None, ArchiveReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["image_like_format"]:
            from dedoc.converters import PNGConverter
            from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
            from dedoc.metadata_extractors import ImageMetadataExtractor
            converter, reader, metadata_extractor = PNGConverter(), PdfImageReader(), ImageMetadataExtractor()
        elif extension in supported_extensions["pdf_like_format"]:
            if self.parsing_params.get("pdf_with_text_layer", None) == "true":
                from dedoc.converters import PDFConverter
                from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
                from dedoc.metadata_extractors import PdfMetadataExtractor
                converter, reader, metadata_extractor = PDFConverter(), PdfTxtlayerReader(), PdfMetadataExtractor()
            if self.parsing_params.get("pdf_with_text_layer", None) == "tabby":
                from dedoc.converters import PDFConverter
                from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
                from dedoc.metadata_extractors import PdfMetadataExtractor
                converter, reader, metadata_extractor = PDFConverter(), PdfTabbyReader(), PdfMetadataExtractor()
            elif self.parsing_params.get("pdf_with_text_layer", None) == "false":
                from dedoc.converters import PNGConverter
                from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
                from dedoc.metadata_extractors import PdfMetadataExtractor
                converter, reader, metadata_extractor = PNGConverter(), PdfImageReader(), PdfMetadataExtractor()
            elif self.parsing_params.get("pdf_with_text_layer", None) in ["auto", "auto_tabby", None]:
                from dedoc.converters import PDFConverter
                from dedoc.readers.pdf_reader.pdf_auto_reader.pdf_auto_reader import PdfAutoReader
                from dedoc.metadata_extractors import PdfMetadataExtractor
                converter, reader, metadata_extractor = PDFConverter(), PdfAutoReader(), PdfMetadataExtractor()
        elif extension in supported_extensions["csv_like_format"]:
            from dedoc.readers import CSVReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = None, CSVReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["txt_like_format"]:
            from dedoc.converters import TxtConverter
            from dedoc.readers import RawTextReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = TxtConverter(), RawTextReader(), BaseMetadataExtractor()
        elif extension in supported_extensions["json_like_format"]:
            from dedoc.readers import JsonReader
            from dedoc.metadata_extractors import BaseMetadataExtractor
            converter, reader, metadata_extractor = None, JsonReader(), BaseMetadataExtractor()

        if self.split in ["line", "page"]:
            from dedoc.structure_constructors import LinearConstructor
            constructors, default_constructor = {"linear": LinearConstructor()}, LinearConstructor()
        else:
            from dedoc.structure_constructors import TreeConstructor
            constructors, default_constructor = {"tree": TreeConstructor()}, TreeConstructor()

        from dedoc.converters import ConverterComposition
        from dedoc.readers import ReaderComposition
        from dedoc.structure_extractors import StructureExtractorComposition
        from dedoc.structure_constructors import StructureConstructorComposition
        from dedoc.structure_extractors import DefaultStructureExtractor
        from dedoc.attachments_handler import AttachmentsHandler
        from dedoc.metadata_extractors import MetadataExtractorComposition

        try:
            manager_config = dict(
                converter=ConverterComposition(converters=[converter]),
                reader=ReaderComposition(readers=[reader]),
                structure_extractor=StructureExtractorComposition(extractors={"other": DefaultStructureExtractor()}, default_key="other"),
                structure_constructor=StructureConstructorComposition(constructors=constructors, default_constructor=default_constructor),
                document_metadata_extractor=MetadataExtractorComposition(extractors=[metadata_extractor]),
                attachments_handler=AttachmentsHandler()
            )
        except BadFileFormatError as e:
            print(f'Could not read file {self.file_path} with mime = "{mime}", extension = "{extension}" ({e}).')  # noqa: T201
            manager_config = None
        return manager_config

    def lazy_load(  # noqa: FOL005
        self,
    ) -> Iterator[Document]:
        """Lazily load documents."""
        yield from self.parser.parse(self.file_path, parsing_parameters=self.parsing_params, split=self.split)
