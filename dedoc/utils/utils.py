import datetime
import difflib
import gzip
import hashlib
import mimetypes
import os
import random
import re
import time
import requests
import json
from os.path import splitext
from typing import List, Optional, TypeVar, Tuple, Iterable, Iterator, Dict, Any

from Levenshtein._levenshtein import ratio
from dateutil.parser import parse
from charset_normalizer import from_bytes

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.tree_node import TreeNode
from dedoc.data_structures.hierarchy_level import HierarchyLevel

T = TypeVar("T")


def list_get(ls: List[T], index: int, default: Optional[T] = None) -> Optional[T]:
    if 0 <= index < len(ls):
        return ls[index]
    return default


def flatten(data: List[List[T]]) -> Iterable[T]:
    for group in data:
        for item in group:
            yield item


def identity(x: T) -> T:
    return x


def get_batch(size: int, iterable: Iterator[T]) -> Iterator[List[T]]:
    """
    it is batch generator. Generating batch with 'size'. Last batch can be less then size or equals []
    :param size: batch size
    :param iterable: input data iterator
    :return: iterator of element of current batch
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if len(batch) > 0:
        yield batch


def splitext_(path: str) -> Tuple[str, str]:
    """
    get extensions with several dots
    """
    if len(path.split('.')) > 2:
        return path.split('.')[0], '.' + '.'.join(path.split('.')[-2:])
    return splitext(path)


def _text_from_item(item: dict) -> str:
    res = item.get("text", "")
    if "subparagraphs" in item:
        res += "\n".join(_text_from_item(_) for _ in item["subparagraphs"])
    return res


def document2txt(doc: dict) -> str:
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


def get_extensions_by_mime(mime: str) -> List[str]:
    return mimetypes.guess_all_extensions(mime)


def get_extensions_by_mimes(mimes: List[str]) -> List[str]:
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
                           metadata=LineMetadata(page_id=0, line_id=0, hierarchy_level=HierarchyLevel.create_root()),
                           subparagraphs=[],
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
        dammit = from_bytes(blob)
        return dammit.best().encoding
    except:  # noqa  ignore exception and return default encoding
        return default


def similarity(s1: str, s2: str) -> float:
    """string similarity"""
    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


def similarity_levenshtein(str1: str, str2: str) -> float:
    str1 = str1.lower()
    str2 = str2.lower()
    return ratio(str1, str2)


def convert_datetime(time_string: str) -> int:
    """
    convert string_time in ISO/IEC 8824 format into UnixTime
    :param time_str: string of time in ISO/IEC 8824 format (D:YYYYMMDDHHmmSSOHH'mm'). Example: "D:20210202145619+00'16'"
    :return: UnixTime (type: int)
    """
    # convert utc-part OHH'mm' into iso-format ±HHMM[SS[.ffffff]] 'D:20191028113639Z'
    # description of time-format can see
    # https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf, page 160

    date = str(time_string).replace("D:", "")
    if re.match(r"\d{14}(\+|-)\d{2}'?\d{2}'?", date):
        date_format = "%Y%m%d%H%M%S%z"
        d = datetime.datetime.strptime(date.replace("'", ""), date_format)
    elif re.match(r"\d{14}(Z|z)\d{2}'?\d{2}'?", date):
        date_format = "%Y%m%d%H%M%S"
        date = date.split("Z")[0]
        d = datetime.datetime.strptime(date.replace("'", ""), date_format)
    else:
        d = parse(date, fuzzy=True)

    return int(d.timestamp())


def check_filename_length(filename: str) -> str:
    max_filename_length = 255  # posix name limitation
    if len(filename) > max_filename_length:
        name, ext = splitext_(filename)
        filename = name[:max_filename_length - len(ext)] + ext

    return filename


def send_file(host: str, file_name: str, file_path: str, parameters: dict) -> Dict[str, Any]:
    with open(file_path, 'rb') as file:
        # file we want to parse
        files = {'file': (file_name, file)}
        # dict with additional parameters
        # and now we send post request with attached file and parameters.
        r = requests.post("{}/upload".format(host), files=files, data=parameters)
        # wait for response, parse json result and print it
        assert r.status_code == 200
        result = json.loads(r.content.decode())
        return result
