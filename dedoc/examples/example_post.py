import json
import os
from pprint import pprint

import requests

# We want to parse file example.docx
# We will send it with requests lib
file_name = "example.docx"
file_path = os.path.abspath(file_name)

with open(file_path, 'rb') as file:
    # file we want to parse
    files = {'file': (file_name, file)}
    # dict with additional parameters
    data = {"document_type": "example"}
    # and now we send post request with attached file and paremeters.
    r = requests.post("http://localhost:1231/upload", files=files, data=data)
    # wait for response, parse json result and print it
    result = json.loads(r.content.decode())
    pprint(result)
