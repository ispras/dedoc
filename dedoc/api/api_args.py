# noqa
from typing import Any, Optional
from fastapi import Body
from pydantic import BaseModel


class QueryParameters(BaseModel):
    document_type: Optional[str]
    structure_type: Optional[str]
    return_format: Optional[str]

    with_attachments: Optional[str]
    need_content_analysis: Optional[str]
    recursion_deep_attachments: Optional[str]
    return_base64: Optional[str]

    insert_table: Optional[str]
    need_pdf_table_analysis: Optional[str]
    table_type: Optional[str]
    orient_analysis_cells: Optional[str]
    orient_cell_angle: Optional[str]

    pdf_with_text_layer: Optional[str]
    language: Optional[str]
    pages: Optional[str]
    is_one_column_document: Optional[str]
    document_orientation: Optional[str]
    need_header_footer_analysis: Optional[str]
    need_binarization: Optional[str]

    delimiter: Optional[str]
    encoding: Optional[str]
    html_fields: Optional[str]
    handle_invisible_table: Optional[str]

    def __init__(self,
                 # type of document structure parsing
                 document_type: Optional[str] = Body(description="a document type. Default: ''", enum=["", "law", "tz", "diploma"], default=None),
                 structure_type: Optional[str] = Body(description="output structure type (linear or tree). Default: 'tree'", enum=["linear", "tree"], default=None),
                 return_format: Optional[str] = Body(description="an option for returning a response in html form, json, pretty_json or tree. Assume that one should use json in all cases, all other formats are used for debug porpoises only. Default: 'json'", default=None),

                 # attachments handling
                 with_attachments: Optional[str] = Body(description="an option to enable the analysis of attached files. Default: 'false'", default=None),
                 need_content_analysis: Optional[str] = Body(description="turn on if you need parse the contents of the document attachments. Default: 'false'", default=None),
                 recursion_deep_attachments: Optional[str] = Body(description="the depth on which nested attachments will be parsed if need_content_analysis=true. Default: '10'", default=None),
                 return_base64: Optional[str] = Body(description="returns images in base64 format. Default: 'false'", default=None),

                 # tables handling
                 insert_table: Optional[str] = Body(description="Insert table into the result tree's content or not. Default: 'false'", default=None),
                 need_pdf_table_analysis: Optional[str] = Body(description="include a table analysis into pdfs. Default: 'true'", default=None),
                 table_type: Optional[str] = Body(description="a pipeline mode for a table recognition. Default: ''", default=None),
                 orient_analysis_cells: Optional[str] = Body(description="a table recognition option enables analysis of rotated cells in table headers. Default: 'false'", default=None),
                 orient_cell_angle: Optional[str] = Body(description="an option to set orientation of cells in table headers. \"270\" - cells are rotated 90 degrees clockwise, \"90\" - cells are rotated 90 degrees counterclockwise (or 270 clockwise)", default=None),

                 # pdf handling
                 pdf_with_text_layer: Optional[str] = Body(description="an option to extract text from a text layer to PDF or using OCR methods for image-documents. Default: 'auto_tabby'", enum=["true", "false", "auto", "auto_tabby", "tabby"], default=None),
                 language: Optional[str] = Body(description="a recognition language. Default: 'rus+eng'", enum=["rus+eng", "rus", "eng"], default=None),
                 pages: Optional[str] = Body(description="an option to limit page numbers in pdf, archives with images. left:right, read pages from left to right. Default: ':'", default=None),
                 is_one_column_document: Optional[str] = Body(description="an option to set one or multiple column document. \"auto\" - system predict number of columns in document pages, \"true\" - is one column documents, \"false\" - is multiple column documents. Default: 'auto'", default=None),
                 document_orientation: Optional[str] = Body(description="an option to set vertical orientation of the document without using an orientation classifier \"auto\" - system predict angle (0, 90, 180, 270) and rotate document, \"no_change\" - do not predict orientation. Default: 'auto'", enum=["auto", "no_change"], default=None),
                 need_header_footer_analysis: Optional[str] = Body(description="include header-footer analysis into pdf with text layer. Default: 'false'", default=None),
                 need_binarization: Optional[str] = Body(description="include an adaptive binarization into pdf without a text layer. Default: 'false'", default=None),

                 # other formats handling
                 delimiter: Optional[str] = Body(description="a column separator for csv-files", default=None),
                 encoding: Optional[str] = Body(description="a document encoding", default=None),
                 html_fields: Optional[str] = Body(description="a list of fields for JSON documents to be parsed as HTML documents. It is written as a json string of a list, where each list item is a list of keys to get the field. Default: ''", default=None),
                 handle_invisible_table: Optional[str] = Body(description="handle table without visible borders as tables in html. Default: 'false'", default=None),


                 **data: Any) -> None:

        super().__init__(**data)
        self.document_type: str                 = document_type or ""
        self.structure_type: str                = structure_type or 'tree'
        self.return_format: str                 = return_format or 'json'

        self.with_attachments: str              = with_attachments or 'false'
        self.need_content_analysis: str         = need_content_analysis or 'false'
        self.recursion_deep_attachments: str    = recursion_deep_attachments or '10'
        self.return_base64: str                 = return_base64 or 'false'

        self.insert_table: str                  = insert_table or 'false'
        self.need_pdf_table_analysis: str       = need_pdf_table_analysis or 'true'
        self.table_type: str                    = table_type or ''
        self.orient_analysis_cells: str         = orient_analysis_cells or 'false'
        self.orient_cell_angle: str             = orient_cell_angle or "90"

        self.pdf_with_text_layer: str           = pdf_with_text_layer or 'auto_tabby'
        self.language: str                      = language or "rus+eng"
        self.pages: str                         = pages or ':'
        self.is_one_column_document: str        = is_one_column_document or 'auto'
        self.document_orientation: str          = document_orientation or "auto"
        self.need_header_footer_analysis: str   = need_header_footer_analysis or 'false'
        self.need_binarization: str             = need_binarization or 'false'

        self.delimiter: str                     = delimiter
        self.encoding: str                      = encoding
        self.html_fields: str                   = html_fields or ''
        self.handle_invisible_table: str        = handle_invisible_table or 'false'
