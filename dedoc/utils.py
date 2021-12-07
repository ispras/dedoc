import gzip
import hashlib
import os
import re
import time
import random
import mimetypes
from os.path import splitext
from typing import List, Tuple, Optional

from bs4 import UnicodeDammit

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.tree_node import TreeNode
from dedoc.structure_parser.heirarchy_level import HierarchyLevel


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


def special_match(strg: str, regular_pattern: str = r'[^.?!,:;"\'\n\r ]') -> bool:
    """
    checks if a string only contains certain characters
    """
    search = re.compile(regular_pattern).search
    return not bool(search(strg))


def calculate_file_hash(path: str) -> str:
    with open(path, "rb") as file:
        file_hash = hashlib.md5()
        chunk = file.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = file.read(8192)
    return str(file_hash.hexdigest())


def get_empty_content() -> DocumentContent:
    return DocumentContent(
        tables=[],
        structure=TreeNode(node_id="0",
                           text="",
                           annotations=[],
                           metadata=ParagraphMetadata(
                               paragraph_type=HierarchyLevel.root,
                               predicted_classes=None,
                               page_id=0,
                               line_id=0,
                           ),
                           subparagraphs=[],
                           hierarchy_level=HierarchyLevel.create_root(),
                           parent=None)
    )


def get_encoding(path: str, default: str = None) -> Optional[str]:
    """
    try to define encoding of the given file
    """
    try:
        if path.endswith(".gz"):
            with gzip.open(path, "r") as file:
                blob = file.read()
        else:
            with open(path, "rb") as file:
                blob = file.read()
        dammit = UnicodeDammit(blob)
        return dammit.original_encoding
    except:  # noqa  ignore exception and return default encoding
        return default
