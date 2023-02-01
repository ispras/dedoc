from typing import Any

from flask_restx import Api
from werkzeug.datastructures import FileStorage


def init_args(api: Api, file_required: bool = True) -> Any:
    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files', help="input binary file",
                               type=FileStorage, required=file_required)
    upload_parser.add_argument('language', type=str,
                               help="recognition language", required=False,
                               default="rus+eng", choices=["rus+eng", "rus", "eng"])
    upload_parser.add_argument("with_attachments", type=str, required=False,
                               help="option to enable analysis of attached files.", default="false")
    upload_parser.add_argument("insert_table", type=str, required=False,
                               help="option to enable analysis of attached files.", default="false")
    upload_parser.add_argument("return_format", type=str, required=False,
                               help="an option to return the response in html form, json, pretty_json or tree. "
                                    "Assume that one should use json in all cases, all other formats are used for debug"
                                    " porpoises only",
                               default="json")
    upload_parser.add_argument("structure_type", type=str, required=False,
                               help="output structure type (linear or tree)", choices=["linear", "tree"])
    upload_parser.add_argument("delimiter", type=str, required=False, help="column separator for csv-files")

    upload_parser.add_argument("encoding", type=str, required=False, help="document encoding")

    upload_parser.add_argument("document_type", type=str, required=False,
                               help="document type", choices=["", "law", "tz", "diploma", "article", "slide"]),
    upload_parser.add_argument("pdf_with_text_layer", type=str, required=False,
                               help="option to extract text from a text layer to PDF or using OCR methods from "
                                    "image documents.", choices=["true", "auto", "auto_tabby", "false", "tabby"])
    upload_parser.add_argument("pages", type=str, required=False,
                               help=("option to limit page numbers in pdf, archives with images. left:right, read pages"
                                     " from left to right "),
                               default=":")
    upload_parser.add_argument("orient_analysis_cells", type=str, required=False,
                               help="table recognition option enables analysis of rotated cells in table headers.",
                               default="false")
    upload_parser.add_argument("orient_cell_angle", type=str, required=False,
                               help="option to set orientation of cells in table headers. "
                                    "\"270\" - cells are rotated 90 degrees clockwise, "
                                    "\"90\" - cells are rotated 90 degrees counterclockwise (or 270 clockwise)",
                               default="90", choices=["90", "270"])
    upload_parser.add_argument("is_one_column_document", type=str, required=False,
                               help="option to set one or multiple column document. "
                                    "\"auto\" - system predict number of columns in document pages, "
                                    "\"true\" - is one column documents, "
                                    "\"false\" - is multiple column documents",
                               default="auto", choices=["auto", "true", "false"])

    upload_parser.add_argument("html_fields", type=str, required=False,
                               help="a list of fields for JSON documents to be parsed as HTML documents. "
                                    "It is written as a json string of a list, where each list item is a list of keys "
                                    "to get the field.",
                               default="")
    upload_parser.add_argument("cloud_bucket", type=str, required=False,
                               help="path (bucket) in the cloud storage mime", default="")

    upload_parser.add_argument("need_header_footer_analysis", type=str, required=False,
                               help="include header-footer analysis into pdf with text layer", default="false")

    upload_parser.add_argument("need_text_localization", type=str, required=False,
                               help="include text localization into pdf without text layer", default="false")

    upload_parser.add_argument("need_pdf_table_analysis", type=str, required=False,
                               help="include table analysis into pdfs", default="true")
    upload_parser.add_argument("handle_invisible_table", type=str, required=False,
                               help="handle table without visible borders as  table in html", default="false")

    upload_parser.add_argument("return_base64", type=str, required=False,
                               help="returns images in base64 format", default="false")

    upload_parser.add_argument("archive_as_single_file", type=str, required=False,
                               help="additional parameters for archive reader", default="true")

    upload_parser.add_argument("upload_attachments_into_cloud", type=str, required=False,
                               help="on if you need upload attachments into cloud. On if with_attachments=True and "
                                    "\"cloud_bucket\" not empty",
                               default="false")

    upload_parser.add_argument("table_type", type=str, required=False, help="pipline for table recognition",
                               default="")

    return upload_parser
