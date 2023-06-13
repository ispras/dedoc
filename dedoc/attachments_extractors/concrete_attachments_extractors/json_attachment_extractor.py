import os
import json
from typing import List, Optional

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile


class JsonAttachmentsExtractor(AbstractAttachmentsExtractor):
    """
    Extract attachments from json files.
    """
    def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if this extractor can get attachments from the document (it should have .json extension)
        """
        return extension.lower().endswith(".json")

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Get attachments from the given json document.
        Attached files are html files if the option `html_fields` is given in the `parameters`.
        This option should contain list of lists of keys converted to string.
        The list of keys is the path to the html content inside the json file (end node should be string),
        that needs to be converted into a file attachment.

        For example:

        For json like {"a": {"b": "Some html string"}, "c": "Another html string"}

        the possible value for `html_fields` parameter is '[["a", "b"], ["c"]]'.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        attachments = []

        with open(os.path.join(tmpdir, filename)) as f:
            data = json.load(f)

        field_keys = json.loads(parameters.get("html_fields")) if parameters.get("html_fields") else []

        for keys in field_keys:
            path = json.dumps(keys, ensure_ascii=False)
            attached_filename = path + '.html'
            attachment_file_path = os.path.join(tmpdir, attached_filename)
            field_content = self.__get_value_by_keys(data, keys)

            if not isinstance(field_content, str):
                continue

            with open(attachment_file_path, 'w') as f:
                f.write(field_content)

            with open(attachment_file_path, mode='rb') as f:
                binary_data = f.read()

            attachments.append((attached_filename, binary_data))

        need_content_analysis = str(parameters.get("need_content_analysis", "false")).lower() == "true"
        return self._content2attach_file(content=attachments, tmpdir=tmpdir, need_content_analysis=need_content_analysis)

    def __get_value_by_keys(self, data: dict, keys: List[str]) -> dict:
        value = data

        for key in keys:
            value = value[key]

        return value
