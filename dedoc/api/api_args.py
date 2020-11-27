from typing import Any

from flask_restplus import Api
from werkzeug.datastructures import FileStorage


def init_args(api: Api) -> Any:
    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files', help="input binary file",
                               type=FileStorage, required=True)
    upload_parser.add_argument('language', type=str,
                               help="recognition language", required=False,
                               default="rus+eng", choices=["rus+eng", "rus", "eng"])
    upload_parser.add_argument("with_attachments", type=bool, required=False,
                               help="option to enable analysis of attached files.", default=False)
    upload_parser.add_argument("return_html", type=bool, required=False,
                               help="an option to return the response in html form.", default=False)
    upload_parser.add_argument("document_type", type=str, required=False,
                               help="document type", default="", choices=["", "law", "article"])
    upload_parser.add_argument("structure_type", type=str, required=False,
                               help="output structure type (linear or tree)", default="linear",
                               choices=["linear", "tree"])

    return upload_parser
