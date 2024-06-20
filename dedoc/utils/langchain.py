from dedoc.extensions import converted_extensions, recognized_extensions


supported_extensions = {format_group: {*recognized_extensions._asdict()[format_group], *converted_extensions._asdict()[format_group]} for format_group in recognized_extensions._asdict().keys()}  # noqa


def make_manager_config(file_path: str, split: str, parsing_params: dict) -> dict:  # noqa: C901
    from dedoc.utils.utils import get_mime_extension
    from dedoc.common.exceptions.bad_file_error import BadFileFormatError

    mime, extension = get_mime_extension(file_path=file_path)

    if extension in supported_extensions["excel_like_format"]:
        from dedoc.converters.concrete_converters.excel_converter import ExcelConverter
        from dedoc.readers.excel_reader.excel_reader import ExcelReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = ExcelConverter(), ExcelReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["docx_like_format"]:
        from dedoc.converters.concrete_converters.docx_converter import DocxConverter
        from dedoc.readers.docx_reader.docx_reader import DocxReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.docx_metadata_extractor import DocxMetadataExtractor
        converter, reader, metadata_extractor = DocxConverter(), DocxReader(), DocxMetadataExtractor()
    elif extension in supported_extensions["pptx_like_format"]:
        from dedoc.converters.concrete_converters.pptx_converter import PptxConverter
        from dedoc.readers.pptx_reader.pptx_reader import PptxReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = PptxConverter(), PptxReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["html_like_format"]:
        from dedoc.readers.html_reader.html_reader import HtmlReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = None, HtmlReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["eml_like_format"]:
        from dedoc.readers.email_reader.email_reader import EmailReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = None, EmailReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["mhtml_like_format"]:
        from dedoc.readers.mhtml_reader.mhtml_reader import MhtmlReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = None, MhtmlReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["archive_like_format"]:
        from dedoc.readers.archive_reader.archive_reader import ArchiveReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = None, ArchiveReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["image_like_format"]:
        from dedoc.converters.concrete_converters.png_converter import PNGConverter
        from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.image_metadata_extractor import ImageMetadataExtractor
        converter, reader, metadata_extractor = PNGConverter(), PdfImageReader(), ImageMetadataExtractor()
    elif extension in supported_extensions["pdf_like_format"]:
        from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer
        from dedoc.converters.concrete_converters.pdf_converter import PDFConverter
        from dedoc.metadata_extractors.concrete_metadata_extractors.pdf_metadata_extractor import PdfMetadataExtractor
        pdf_with_text_layer = get_param_pdf_with_txt_layer(parsing_params)
        if pdf_with_text_layer == "true":
            from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
            converter, reader, metadata_extractor = PDFConverter(), PdfTxtlayerReader(), PdfMetadataExtractor()
        elif pdf_with_text_layer == "tabby":
            from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
            converter, reader, metadata_extractor = PDFConverter(), PdfTabbyReader(), PdfMetadataExtractor()
        elif pdf_with_text_layer == "false":
            from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
            converter, reader, metadata_extractor = PDFConverter(), PdfImageReader(), PdfMetadataExtractor()
        else:
            from dedoc.readers.pdf_reader.pdf_auto_reader.pdf_auto_reader import PdfAutoReader
            converter, reader, metadata_extractor = PDFConverter(), PdfAutoReader(), PdfMetadataExtractor()
    elif extension in supported_extensions["csv_like_format"]:
        from dedoc.readers.csv_reader.csv_reader import CSVReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = None, CSVReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["txt_like_format"]:
        from dedoc.converters.concrete_converters.txt_converter import TxtConverter
        from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = TxtConverter(), RawTextReader(), BaseMetadataExtractor()
    elif extension in supported_extensions["json_like_format"]:
        from dedoc.readers.json_reader.json_reader import JsonReader
        from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
        converter, reader, metadata_extractor = None, JsonReader(), BaseMetadataExtractor()
    else:
        raise BadFileFormatError(f'Could not find the suitable reader for the file with mime = "{mime}", extension = "{extension}".')  # noqa: T201

    if split in ["line", "page", "document"]:
        from dedoc.structure_constructors.concrete_structure_constructors.linear_constructor import LinearConstructor
        constructors, default_constructor = {"linear": LinearConstructor()}, LinearConstructor()
    else:
        from dedoc.structure_constructors.concrete_structure_constructors.tree_constructor import TreeConstructor
        constructors, default_constructor = {"tree": TreeConstructor()}, TreeConstructor()

    from dedoc.converters.converter_composition import ConverterComposition
    from dedoc.readers.reader_composition import ReaderComposition
    from dedoc.structure_extractors.structure_extractor_composition import StructureExtractorComposition
    from dedoc.structure_constructors.structure_constructor_composition import StructureConstructorComposition
    from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
    from dedoc.attachments_handler.attachments_handler import AttachmentsHandler
    from dedoc.metadata_extractors.metadata_extractor_composition import MetadataExtractorComposition

    # hardcoding some arguments
    parsing_params["need_pdf_table_analysis"] = False
    parsing_params["with_attachments"] = False
    parsing_params["need_content_analysis"] = False
    parsing_params["document_type"] = "other"
    parsing_params["structure_type"] = "linear" if split in ["line", "page", "document"] else "tree"

    manager_config = dict(
        converter=ConverterComposition(converters=[converter] if converter else []),
        reader=ReaderComposition(readers=[reader]),
        structure_extractor=StructureExtractorComposition(extractors={"other": DefaultStructureExtractor()}, default_key="other"),
        structure_constructor=StructureConstructorComposition(constructors=constructors, default_constructor=default_constructor),
        document_metadata_extractor=MetadataExtractorComposition(extractors=[metadata_extractor]),
        attachments_handler=AttachmentsHandler()
    )
    return manager_config


def make_manager_pdf_config(file_path: str, split: str, parsing_params: dict) -> dict:  # noqa: C901
    from dedoc.utils.utils import get_mime_extension
    from dedoc.common.exceptions.bad_file_error import BadFileFormatError

    mime, extension = get_mime_extension(file_path=file_path)

    if extension in supported_extensions["pdf_like_format"]:
        from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer
        from dedoc.converters.concrete_converters.pdf_converter import PDFConverter
        from dedoc.metadata_extractors.concrete_metadata_extractors.pdf_metadata_extractor import PdfMetadataExtractor
        pdf_with_text_layer = get_param_pdf_with_txt_layer(parsing_params)
        if pdf_with_text_layer == "true":
            from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
            converter, reader, metadata_extractor = PDFConverter(), PdfTxtlayerReader(), PdfMetadataExtractor()
        elif pdf_with_text_layer == "tabby":
            from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
            converter, reader, metadata_extractor = PDFConverter(), PdfTabbyReader(), PdfMetadataExtractor()
        elif pdf_with_text_layer == "false":
            from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
            converter, reader, metadata_extractor = PDFConverter(), PdfImageReader(), PdfMetadataExtractor()
        else:
            from dedoc.readers.pdf_reader.pdf_auto_reader.pdf_auto_reader import PdfAutoReader
            converter, reader, metadata_extractor = PDFConverter(), PdfAutoReader(), PdfMetadataExtractor()
    else:
        raise BadFileFormatError(f'Could not find the suitable reader for the file with mime = "{mime}", extension = "{extension}".')  # noqa: T201

    if split in ["line", "page", "document"]:
        from dedoc.structure_constructors.concrete_structure_constructors.linear_constructor import LinearConstructor
        constructors, default_constructor = {"linear": LinearConstructor()}, LinearConstructor()
    else:
        from dedoc.structure_constructors.concrete_structure_constructors.tree_constructor import TreeConstructor
        constructors, default_constructor = {"tree": TreeConstructor()}, TreeConstructor()

    from dedoc.converters.converter_composition import ConverterComposition
    from dedoc.readers.reader_composition import ReaderComposition
    from dedoc.structure_extractors.structure_extractor_composition import StructureExtractorComposition
    from dedoc.structure_constructors.structure_constructor_composition import StructureConstructorComposition
    from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
    from dedoc.attachments_handler.attachments_handler import AttachmentsHandler
    from dedoc.metadata_extractors.metadata_extractor_composition import MetadataExtractorComposition

    # hardcoding some arguments
    parsing_params["need_pdf_table_analysis"] = False
    parsing_params["with_attachments"] = False
    parsing_params["need_content_analysis"] = False
    parsing_params["document_type"] = "other"
    parsing_params["structure_type"] = "linear" if split in ["line", "page", "document"] else "tree"

    manager_config = dict(
        converter=ConverterComposition(converters=[converter]),
        reader=ReaderComposition(readers=[reader]),
        structure_extractor=StructureExtractorComposition(extractors={"other": DefaultStructureExtractor()}, default_key="other"),
        structure_constructor=StructureConstructorComposition(constructors=constructors, default_constructor=default_constructor),
        document_metadata_extractor=MetadataExtractorComposition(extractors=[metadata_extractor]),
        attachments_handler=AttachmentsHandler()
    )
    return manager_config
