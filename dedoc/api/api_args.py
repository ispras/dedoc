from dataclasses import asdict, dataclass
from typing import Optional

from fastapi import Form


@dataclass
class QueryParameters:
    # type of document structure parsing
    document_type: str = Form("", enum=["", "law", "tz", "diploma"], description="Document domain")
    structure_type: str = Form("tree", enum=["linear", "tree"], description="Output structure type")
    return_format: str = Form("json", enum=["json", "html", "plain_text", "tree", "collapsed_tree", "ujson", "pretty_json"],
                              description="Response representation, most types (except json) are used for debug purposes only")

    # attachments handling
    with_attachments: str = Form("false", enum=["true", "false"], description="Enable attached files extraction")
    need_content_analysis: str = Form("false", enum=["true", "false"], description="Enable parsing contents of the attached files")
    recursion_deep_attachments: str = Form("10", description="Depth on which nested attachments will be parsed if need_content_analysis=true")
    return_base64: str = Form("false", enum=["true", "false"], description="Save attached images to the document metadata in base64 format")
    attachments_dir: Optional[str] = Form(None, description="Path to the directory where to save files' attachments")

    # tables handling
    need_pdf_table_analysis: str = Form("true", enum=["true", "false"], description="Enable table recognition for pdf")
    table_type: str = Form("", description="Pipeline mode for table recognition")
    orient_analysis_cells: str = Form("false", enum=["true", "false"], description="Enable analysis of rotated cells in table headers")
    orient_cell_angle: str = Form("90", enum=["90", "270"],
                                  description='Set cells orientation in table headers, "90" means 90 degrees counterclockwise cells rotation')

    # pdf handling
    pdf_with_text_layer: str = Form("auto_tabby", enum=["true", "false", "auto", "auto_tabby", "tabby"],
                                    description="Extract text from a text layer of PDF or using OCR methods for image-like documents")
    language: str = Form("rus+eng", enum=["rus+eng", "rus", "eng"], description="Recognition language")
    pages: str = Form(":", description='Page numbers range for reading PDF or images, "left:right" means read pages from left to right')
    is_one_column_document: str = Form("auto", enum=["auto", "true", "false"],
                                       description='One or multiple column document, "auto" - predict number of page columns automatically')
    document_orientation: str = Form("auto", enum=["auto", "no_change"],
                                     description='Orientation of the document pages, "auto" - predict orientation (0, 90, 180, 270 degrees), '
                                                 '"no_change" - set vertical orientation of the document without using an orientation classifier')
    need_header_footer_analysis: str = Form("false", enum=["true", "false"], description="Exclude headers and footers from PDF parsing result")
    need_binarization: str = Form("false", enum=["true", "false"], description="Binarize document pages (for images or PDF without a textual layer)")

    # other formats handling
    delimiter: Optional[str] = Form(None, description="Column separator for CSV files")
    encoding: Optional[str] = Form(None, description="Document encoding")
    html_fields: str = Form("", description="List of fields for JSON documents to be parsed as HTML documents")
    handle_invisible_table: str = Form("false", enum=["true", "false"], description="Handle tables without visible borders as tables in HTML")

    def to_dict(self) -> dict:
        parameters = {}

        for parameter_name, parameter_value in asdict(self).items():
            parameters[parameter_name] = getattr(parameter_value, "default", parameter_value)

        return parameters
