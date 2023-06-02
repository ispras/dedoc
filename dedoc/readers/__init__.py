from .archive_reader.archive_reader import ArchiveReader
from .base_reader import BaseReader
from .csv_reader.csv_reader import CSVReader
from .docx_reader.docx_reader import DocxReader
from .excel_reader.excel_reader import ExcelReader
from .html_reader.html_reader import HtmlReader
from .json_reader.json_reader import JsonReader
from .mhtml_reader.mhtml_reader import MhtmlReader
from .pptx_reader.pptx_reader import PptxReader
from .reader_composition import ReaderComposition
from .pdf_reader.pdf_base_reader import PdfBaseReader
from .pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
from .pdf_reader.pdf_txtlayer_reader.tabby_pdf_reader import TabbyPDFReader
from .pdf_reader.auto_pdf_reader.auto_pdf_reader import AutoPdfReader
from .txt_reader.raw_text_reader import RawTextReader

__all__ = ['ArchiveReader', 'BaseReader', 'CSVReader', 'DocxReader', 'ExcelReader', 'HtmlReader', 'JsonReader', 'MhtmlReader', 'PptxReader',
           'ReaderComposition', 'PdfBaseReader', 'PdfImageReader', 'TabbyPDFReader', 'RawTextReader', 'AutoPdfReader']
