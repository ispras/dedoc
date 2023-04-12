from typing import Optional, Any
import ujson as json

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.data_structures.hierarchy_level import HierarchyLevel


class JsonReader(BaseReader):

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str], parameters: Optional[dict] = None) -> bool:
        return extension.lower().endswith(".json")

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        with open(path) as file:
            json_data = json.load(file)
        stack = [(json_data, 1)]
        result = []
        while len(stack) > 0:
            element, depth = stack.pop()
            if isinstance(element, dict) and len(element) > 0:
                self.__handle_dict(depth, element, result, stack)

            if isinstance(element, list) and len(element) > 0:
                self.__handle_list(depth, element, result, stack)
            elif self.__is_flat(element):
                line = self.__handle_one_element(depth=depth,
                                                 value=str(element),
                                                 line_type=HierarchyLevel.raw_text,
                                                 line_type_meta=HierarchyLevel.raw_text)
                result.append(line)

        for line_id, line in enumerate(result):
            line.metadata.line_id = line_id

        return UnstructuredDocument(tables=[], lines=result, attachments=[], warnings=[])

    def __handle_list(self, depth: int, element: list, result: list, stack: list) -> None:
        for _ in range(len(element)):
            sub_element = element.pop(0)
            line = self.__handle_one_element(depth=depth,
                                             value=sub_element,
                                             line_type=HierarchyLevel.list_item,
                                             line_type_meta=HierarchyLevel.list_item)
            result.append(line)
            if not self.__is_flat(sub_element):
                stack.append((element, depth))
                stack.append((sub_element, depth + 1))
                break

    def __handle_dict(self, depth: int, element: dict, result: list, stack: list) -> None:
        for key in sorted(element.keys()):
            # key = min(element.keys()) if len(element) < 100 else list(element.keys())[0]
            value = element.pop(key)
            line = self.__handle_one_element(depth=depth,
                                             value=value,
                                             line_type=key,
                                             line_type_meta=HierarchyLevel.unknown)
            result.append(line)
            if not self.__is_flat(value):
                stack.append((element, depth))
                stack.append((value, depth + 1))
                break

    def __handle_one_element(self, depth: int, value: Any, line_type: str, line_type_meta: str) -> LineWithMeta:
        if depth == 1 and line_type == "title":
            level1 = 0
            level2 = 0
        else:
            level1 = depth
            level2 = 1
        hierarchy_level = HierarchyLevel(level_1=level1, level_2=level2, can_be_multiline=False, line_type=line_type_meta)
        metadata = LineMetadata(tag_hierarchy_level=hierarchy_level, page_id=0, line_id=None)
        line = LineWithMeta(line=self.__get_text(value), metadata=metadata, annotations=[])
        return line

    def __is_flat(self, value: Any) -> bool:
        return not isinstance(value, (dict, list))

    def __get_text(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            return ""
        return str(value)
