from typing import Optional, Tuple

import ujson as json

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.configuration_manager import get_manager_config
from dedoc.readers.base_reader import BaseReader
from dedoc.structure_parser.heirarchy_level import HierarchyLevel


class JsonReader(BaseReader):

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str]) -> bool:
        return extension.endswith(".json") and not document_type

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:
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
                                                 paragraph_type=HierarchyLevel.raw_text,
                                                 paragraph_type_meta=HierarchyLevel.raw_text)
                result.append(line)

        return UnstructuredDocument(tables=[], lines=result), False

    def __handle_list(self, depth: int, element: list, result: list, stack: list):
        for _ in range(len(element)):
            sub_element = element.pop(0)
            line = self.__handle_one_element(depth=depth,
                                             value=sub_element,
                                             paragraph_type=HierarchyLevel.list_item,
                                             paragraph_type_meta=HierarchyLevel.list_item)
            result.append(line)
            if not self.__is_flat(sub_element):
                stack.append((element, depth))
                stack.append((sub_element, depth + 1))
                break

    def __handle_dict(self, depth: int, element: dict, result: list, stack: list):
        for key in sorted(element.keys()):
            # key = min(element.keys()) if len(element) < 100 else list(element.keys())[0]
            value = element.pop(key)
            line = self.__handle_one_element(depth=depth,
                                             value=value,
                                             paragraph_type=key,
                                             paragraph_type_meta=HierarchyLevel.paragraph)
            result.append(line)
            if not self.__is_flat(value):
                stack.append((element, depth))
                stack.append((value, depth + 1))
                break

    def __handle_one_element(self, depth: int, value, paragraph_type: str, paragraph_type_meta):
        if depth == 1 and paragraph_type == "title":
            level1 = 0
            level2 = 0
        else:
            level1 = depth
            level2 = 1
        hierarchy_level = HierarchyLevel(level_1=level1,
                                         level_2=level2,
                                         can_be_multiline=False,
                                         paragraph_type=paragraph_type_meta)
        metadata = get_manager_config()['paragraph_metadata']().full_fields(paragraph_type=paragraph_type,
                                                                          predicted_classes=None,
                                                                          page_id=0,
                                                                          line_id=None)
        line = LineWithMeta(
            line=self.__get_text(value),
            hierarchy_level=hierarchy_level,
            metadata=metadata,
            annotations=[]
        )
        return line

    def __is_flat(self, value):
        return not isinstance(value, (dict, list))

    def __get_text(self, value) -> str:
        if isinstance(value, (dict, list)):
            return ""
        return str(value)
