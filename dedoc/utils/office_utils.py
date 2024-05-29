import os
import re
import zipfile
from typing import Optional

from bs4 import BeautifulSoup

from dedoc.common.exceptions.bad_file_error import BadFileFormatError


def get_bs_from_zip(zip_path: str, xml_path: str, remove_spaces: bool = False) -> Optional[BeautifulSoup]:
    """
    Utility for extracting xml from files of office formats (docx, pptx, xlsx).
    Gets xml BeautifulSoup tree from the given file inside the zip_path.

    :param zip_path: path to the file of the office format (docx, pptx, xlsx)
    :param xml_path: name of file to extract the tree
    :param remove_spaces: remove spaces between tags except <a:t> </a:t> (for pptx)
    :return: BeautifulSoup tree or None if file wasn't found
    """
    try:
        with zipfile.ZipFile(zip_path) as document:
            content = document.read(xml_path)
            content = re.sub(br"\n[\t ]*", b"", content)

            if remove_spaces:
                # remove spaces between tags, don't remove spaces inside pptx text fields: <a:t> </a:t>
                content = re.sub(br"(?<!<a:t)>\s+<", b"><", content)

            soup = BeautifulSoup(content, "xml")
            return soup
    except KeyError:
        return None
    except zipfile.BadZipFile:
        raise BadFileFormatError(f"Bad office file:\n file_name = {os.path.basename(zip_path)}. Seems file is broken")
