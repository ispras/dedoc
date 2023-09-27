import json
import os
from pprint import pprint

import requests

# We want to parse file example.docx
# We will send it with requests lib
# To parse other document types just paste correct file name below
file_name = "example.docx"
file_path = os.path.abspath(file_name)

with open(file_path, 'rb') as file:
    # file we want to parse
    files = {'file': (file_name, file)}
    # dict with additional parameters
    # to parse pdf with text layer add parameter "pdf_with_text_layer":"true"
    data = {"document_type": ""}
    # and now we send post request with attached file and parameters.
    r = requests.post("http://localhost:1231/upload", files=files, data=data)
    # wait for response, parse json result and print it
    result = json.loads(r.content.decode())
    pprint(result)
