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
    upload_parser.add_argument("document_type", type=str, required=False,
                               help="document type", choices=["", "law", "article", "tz"])
    upload_parser.add_argument("structure_type", type=str, required=False,
                               help="output structure type (linear or tree)", choices=["linear", "tree"])
    upload_parser.add_argument("delimiter", type=str, required=False, help="column separator for csv-files")

    return upload_parser
