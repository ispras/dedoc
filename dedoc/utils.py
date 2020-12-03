import os
import time
import random
import mimetypes
from os.path import splitext
from typing import List, Tuple


def splitext_(path: str) -> Tuple[str, str]:
    """
    get extensions with several dots
    """
    if len(path.split('.')) > 2:
        return path.split('.')[0], '.' + '.'.join(path.split('.')[-2:])
    return splitext(path)


def _text_from_item(item: dict):
    res = item.get("text", "")
    if "subparagraphs" in item:
        res += "\n".join(_text_from_item(_) for _ in item["subparagraphs"])
    return res


def document2txt(doc: dict):
    res = doc["header"]
    for item in doc["items"]:
        res += "\n"
        res += _text_from_item(item)
    return res


def get_unique_name(filename: str) -> str:
    """
    Return a unique name by template [timestamp]_[random number 0..1000][extension]
    """
    _, ext = splitext_(filename)
    ts = int(time.time())
    rnd = random.randint(0, 1000)
    return str(ts) + '_' + str(rnd) + ext


def save_data_to_unique_file(directory: str, filename: str, binary_data: bytes) -> str:
    """
    Saving binary data into a unique name by the filename
    :param directory: directory of file (without filename)
    :param filename: name of file (base)
    :param binary_data: data for saving
    :return: filename of saved file
    """
    unique_filename = get_unique_name(filename)
    with open(os.path.join(directory, unique_filename), "wb") as file_disc:
        file_disc.write(binary_data)

    return unique_filename


def get_file_mime_type(path: str) -> str:
    return mimetypes.guess_type(path)[0] or 'application/octet-stream'


def get_extensions_by_mime(mime: str):
    return mimetypes.guess_all_extensions(mime)


def get_extensions_by_mimes(mimes: List[str]):
    exts = []
    for mime in mimes:
        exts.extend(get_extensions_by_mime(mime))
    return exts
