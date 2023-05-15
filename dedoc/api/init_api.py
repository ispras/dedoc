import os
from dedoc.config import Configuration
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

config = Configuration.getInstance().getConfig()

PORT = config["api_port"]

if "static_files_dirs" in config and config["static_files_dirs"] != {}:
    static_path = os.path.abspath(config["static_files_dirs"]["online_docs"])
else:
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/")


static_files_dirs = config.get("static_files_dirs")

app = FastAPI()
app.mount('/static', StaticFiles(directory=config.get("static_path", static_path)), name="static")
