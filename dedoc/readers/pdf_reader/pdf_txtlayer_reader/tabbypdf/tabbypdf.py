import json
import os
import subprocess
from asyncio.log import logger

from dedoc.common.exceptions.java_not_found_error import JavaNotFoundError

TABBY_JAVA_VERSION = "2.0.0"
JAR_NAME = "ispras_tbl_extr.jar"
JAR_DIR = os.path.abspath(os.path.dirname(__file__))
JAVA_NOT_FOUND_ERROR = "`java` command is not found from this Python process. Please ensure Java is installed and PATH is set for `java`"

DEFAULT_CONFIG = {"JAR_PATH": os.path.join(JAR_DIR, JAR_NAME)}


def _jar_path() -> str:
    return os.environ.get("TABBY_JAR", DEFAULT_CONFIG["JAR_PATH"])


def _run(path: str = None, encoding: str = "utf-8") -> bytes:
    args = ["java"] + ["-jar", _jar_path(), "-i", path]

    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, check=True)
        if result.stderr:
            logger.warning(f"Got stderr: {result.stderr.decode(encoding)}")
        return result.stdout
    except FileNotFoundError:
        raise JavaNotFoundError(JAVA_NOT_FOUND_ERROR)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error from tabby-java:\n{e.stderr.decode(encoding)}\n")
        raise


def extract(path: str) -> dict:
    output = _run(path)
    response = output.decode("UTF-8")
    document = json.loads(response)
    return document
