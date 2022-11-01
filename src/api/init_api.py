import os
from flask import Flask
from flask_cors import CORS

from config import Configuration

config = Configuration.getInstance().getConfig()

PORT = config["api_port"]

static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/")
static_files_dirs = config.get("static_files_dirs")

app = Flask(__name__, static_url_path=config.get("static_path", static_path))
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = config["max_content_length"]

external_static_files_path = config.get("external_static_files_path")
if external_static_files_path is not None and not os.path.isdir(external_static_files_path):
    raise Exception("Could not find directory {}, probably config is incorrect".format(external_static_files_path))

favicon_path = config.get("favicon_path")
if favicon_path is not None and not os.path.isfile(favicon_path):
    raise Exception("Could not find file {}, probably config is incorrect".format(favicon_path))
