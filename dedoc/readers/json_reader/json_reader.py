from json import JSONDecodeError
from typing import Any, List, Optional

import ujson as json

from dedoc.attachments_extractors.concrete_attachments_extractors.json_attachment_extractor import JsonAttachmentsExtractor
from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.common.exceptions.bad_parameters_error import BadParametersError
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_mime_extension


class JsonReader(BaseReader):
    """
    This reader allows handle json files.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.attachment_extractor = JsonAttachmentsExtractor(config=self.config)

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader (it has .json extension).
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower().endswith(".json")

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines and attachments, tables remain empty.
        This reader considers json lists as list items and adds this information to the `tag_hierarchy_level`
        of :class:`~dedoc.data_structures.LineMetadata`.
        The dictionaries are processed by creating key line with type `key` and value line as a child.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters
        with open(file_path) as file:
            try:
                json_data = json.load(file)
            except (JSONDecodeError, ValueError):
                raise BadFileFormatError(msg="Seems that json is invalid")

        if "html_fields" in parameters:
            fields = parameters.get("html_fields", "[]")
            try:
                key_fields = json.loads(fields if fields else "[]")
            except (JSONDecodeError, ValueError):
                raise BadParametersError(f"can't read html_fields {fields}")
            json_data = self.__exclude_html_fields(json_data, key_fields)
            attachments = self.attachment_extractor.extract(file_path=file_path, parameters=parameters)
        else:
            attachments = []

        stack = [(json_data, 1)]
        result = []
        while len(stack) > 0:
            element, depth = stack.pop()
            if isinstance(element, dict) and len(element) > 0:
                self.__handle_dict(depth, element, result, stack)

            if isinstance(element, list) and len(element) > 0:
                self.__handle_list(depth, element, result, stack)
            elif self.__is_flat(element):
                line = self.__handle_one_element(depth=depth, value=str(element), line_type=HierarchyLevel.raw_text, line_type_meta=HierarchyLevel.raw_text)
                result.append(line)
        return UnstructuredDocument(tables=[], lines=result, attachments=attachments)

    def __exclude_html_fields(self, json_data: dict, field_keys: List[List[str]]) -> dict:
        for keys in field_keys:
            self.__exclude_key(json_data, keys)

        return json_data

    def __exclude_key(self, json_data: dict, keys: List[str]) -> None:
        data = json_data
        parents = []

        for key in keys[:-1]:
            parents.append((data, key))
            data = data[key]

        del data[keys[-1]]

        for (data, key) in parents[::-1]:
            if not data[key]:
                del data[key]

    def __handle_list(self, depth: int, element: list, result: list, stack: list) -> None:
        for _ in range(len(element)):
            sub_element = element.pop(0)
            line = self.__handle_one_element(depth=depth, value=sub_element, line_type=HierarchyLevel.list_item, line_type_meta=HierarchyLevel.list_item)
            result.append(line)
            if not self.__is_flat(sub_element):
                stack.append((element, depth))
                stack.append((sub_element, depth + 1))
                break

    def __handle_dict(self, depth: int, element: dict, result: list, stack: list) -> None:
        for key in sorted(element.keys()):
            # key = min(element.keys()) if len(element) < 100 else list(element.keys())[0]
            value = element.pop(key)
            line = self.__handle_one_element(depth=depth, value=key, line_type="key", line_type_meta="key")
            result.append(line)
            stack.append((element, depth))

            if value is not None:
                stack.append((value, depth + 1))
            break

    def __handle_one_element(self, depth: int, value: Any, line_type: str, line_type_meta: str) -> LineWithMeta:  # noqa
        if depth == 1 and line_type == "title":
            level1, level2 = 0, 0
        else:
            level1, level2 = depth, 1

        hierarchy_level = HierarchyLevel(level_1=level1, level_2=level2, can_be_multiline=False, line_type=line_type_meta)
        metadata = LineMetadata(tag_hierarchy_level=hierarchy_level, page_id=0, line_id=None)
        line = LineWithMeta(line=self.__get_text(value), metadata=metadata)
        return line

    def __is_flat(self, value: Any) -> bool:  # noqa
        return not isinstance(value, (dict, list))

    def __get_text(self, value: Any) -> str:  # noqa
        if isinstance(value, (dict, list)) or value is None:
            return ""

        return str(value)
