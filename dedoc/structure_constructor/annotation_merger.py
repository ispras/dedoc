import re
from collections import defaultdict
from typing import List, Dict, Union, Optional

from dedoc.data_structures.annotation import Annotation


class Space:

    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end


class ExtendedAnnotation:

    def __init__(self, annotations: List[Annotation] = None, spaces: List[Space] = None) -> None:
        self.annotations = annotations if annotations is not None else []
        self.spaces = spaces if spaces is not None else []
        self.start = self.get_start()
        self.end = self.get_end()

    def add(self, annotation: Union[Annotation, Space]) -> "ExtendedAnnotation":
        self.start = min(annotation.start, self.start) if self.start is not None else annotation.start
        self.end = max(annotation.end, self.end) if self.end is not None else annotation.end
        if isinstance(annotation, Annotation):
            self.annotations.append(annotation)
        else:
            self.spaces.append(annotation)
        return self

    @property
    def name(self) -> str:
        return self.annotations[0].name

    @property
    def value(self) -> str:
        return self.annotations[0].value

    @property
    def extended(self) -> List[Union[Annotation, Space]]:
        return self.annotations + self.spaces

    def get_start(self) -> Optional[int]:
        if len(self.extended) == 0:
            return None
        return min((annotation.start for annotation in self.extended))

    def get_end(self) -> Optional[int]:
        if len(self.extended) == 0:
            return None
        return max((annotation.end for annotation in self.extended))

    def merge(self) -> Optional[Annotation]:
        if len(self.annotations) == 0:
            return None
        else:
            start = min((a.start for a in self.annotations))
            end = max((a.end for a in self.annotations))
            annotation = self.annotations[0]
            return Annotation(start=start, end=end, value=annotation.value, name=annotation.name)


class AnnotationMerger:
    spaces = re.compile(r'\s+')

    def merge_annotations(self, annotations: List[Annotation], text: str) -> List[Annotation]:
        """
        Merge annotations when end of the firs annotation and start of the second match and has same value.
        Used with add_text
        """
        annotations_group_by_name_value = self._group_annotations(annotations).values()
        spaces = [Space(m.start(), m.end()) for m in self.spaces.finditer(text)]

        merged = []
        for annotation_group in annotations_group_by_name_value:
            group = self._merge_one_group(annotations=annotation_group, spaces=spaces)
            merged.extend(group)
        return merged

    def _merge_one_group(self, annotations: List[Annotation], spaces: List[Space]) -> List[Annotation]:
        """
        merge one group annotations, assume that all annotations has the same name and value
        """
        if len(annotations) <= 1:
            return annotations
        self.__check_annotations_group(annotations)
        result = []
        sorted_annotations = sorted(annotations + spaces, key=lambda a: a.start)
        left = 0
        right = 1
        current_annotation = ExtendedAnnotation().add(sorted_annotations[left])
        while right < len(sorted_annotations):
            right_annotation = sorted_annotations[right]
            if current_annotation.end >= right_annotation.start:
                current_annotation.add(right_annotation)
            else:
                result.append(current_annotation)
                current_annotation = ExtendedAnnotation().add(right_annotation)
            right += 1
        result.append(current_annotation)
        result_annotations = (extended.merge() for extended in result)
        return [annotation for annotation in result_annotations if annotation is not None]

    def __check_annotations_group(self, annotations: List[Annotation]) -> None:
        if len(annotations) > 0:
            first = annotations[0]
            first_name_value = first.name, first.value
            same_name_value = all((annotation.name, annotation.value) == first_name_value for annotation in annotations)
            assert same_name_value, "all group items must have the same name and value"

    @staticmethod
    def _group_annotations(annotations: List[Annotation]) -> Dict[str, List[Annotation]]:
        annotations_group_by_value = defaultdict(list)
        for annotation in annotations:
            annotations_group_by_value[(annotation.name, annotation.value)].append(annotation)
        return annotations_group_by_value

    @staticmethod
    def delete_previous_merged(merged: List[Annotation], new_annotations: Annotation) -> List[Annotation]:
        """
            Deleting previous merged annotations which have become unactual with the new merged annotation
        """
        deleted_list = []
        for annotation in merged:
            if annotation.start == new_annotations.start and \
                    annotation.name == new_annotations.name and \
                    annotation.value == new_annotations.value and \
                    annotation.end <= new_annotations.end:
                deleted_list.append(annotation)

        for annotation in deleted_list:
            merged.remove(annotation)

        return merged
