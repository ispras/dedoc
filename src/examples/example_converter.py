# noqa
import os
from werkzeug.datastructures import FileStorage
from config import get_config
from src.manager.dedoc_thread_manager import DedocThreadedManager

version_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION"))
manager = DedocThreadedManager.from_config(config=get_config(), version=open(version_file_path).read().strip())


filename = "example.docx"

with open(filename, 'rb') as fp:
    file = FileStorage(fp, filename=filename)

    parsed_document = manager.parse_file(file, parameters={"document_type": "example"})

    print(parsed_document)
    print(parsed_document.to_dict(old_version=True))
