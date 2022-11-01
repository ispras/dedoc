import re
from typing import Optional, List, Union, Sized
from uuid import uuid1

from src.data_structures.annotation import Annotation
from src.data_structures.paragraph_metadata import ParagraphMetadata
from src.structure_constructor.annotation_merger import AnnotationMerger
from src.structure_parser.heirarchy_level import HierarchyLevel


class LineWithMeta(Sized):

    def __init__(self,
                 line: str,
                 hierarchy_level: Optional[HierarchyLevel],
                 metadata: ParagraphMetadata,
                 annotations: List[Annotation],
                 uid: str = None) -> None:
        """
        Structural unit of document - line (or paragraph) of text and its metadata. One LineWithMeta should not contain
        text from different logical parts of the document (for example document title and raw text of document should not
        lay in the same line) One the other one logical part of the document may be represented by more than one line
        (for example document title may consist of many lines).

        :param line: raw text of the document line
        :param hierarchy_level: special characteristic of line, helps to construct tree-structured representation from
        flat list of lines, define the nesting level of the line. The lower the level of the hierarchy,
        the closer it is to the root.
        :param metadata: line metadata (related to the entire line, as type of the line or page number)
        :param annotations: metadata refers to some part of the text, for example font size of font type and so on.
        :param uid: unique identifier of the line.
        """

        self.__check_hierarchy_level(hierarchy_level)
        self._line = line
        self._hierarchy_level = hierarchy_level
        assert isinstance(metadata, ParagraphMetadata)
        self._metadata = metadata
        self._annotations = annotations
        self._uid = str(uuid1()) if uid is None else uid

    def __len__(self) -> int:
        return len(self.line)

    def __check_hierarchy_level(self, hierarchy_level: HierarchyLevel) -> None:
        if not (hierarchy_level is None or isinstance(hierarchy_level, HierarchyLevel)):
            raise Exception(hierarchy_level)
        assert hierarchy_level is None or hierarchy_level.level_1 is None or hierarchy_level.level_1 >= 0
        if not (hierarchy_level is None or hierarchy_level.level_2 is None or hierarchy_level.level_2 >= 0):
            raise Exception(hierarchy_level)

    def split(self, sep: str) -> List["LineWithMeta"]:
        """
        Split this line into a list of lines, keep annotations consistent.
        This method does not remove any text from the line
        """
        if not sep:
            raise ValueError("empty separator")
        borders = set()
        for group in re.finditer(sep, self.line):
            borders.add(group.end())
        borders.add(0)
        borders.add(len(self.line))
        borders = sorted(borders)
        if len(borders) <= 2:
            return [self]
        result = []
        for start, end in zip(borders[:-1], borders[1:]):
            result.append(self[start:end])
        return result

    def __getitem__(self, index: Union[slice, int]) -> "LineWithMeta":
        if isinstance(index, int):
            if len(self) == 0 or index >= len(self) or index < -len(self):
                raise IndexError("Get item on empty line")
            index %= len(self)
            return self[index: index + 1]
        if isinstance(index, slice):
            start = index.start if index.start else 0
            stop = index.stop if index.stop is not None else len(self)
            step = 1 if index.step is None else index.step
            if start < 0 or stop < 0 or step != 1:
                raise NotImplementedError()
            if start > len(self) or 0 < len(self) == start:
                raise IndexError("start > len(line)")

            annotations = self.__extract_annotations_by_slice(start, stop)
            return LineWithMeta(line=self.line[start: stop],
                                metadata=self.metadata,
                                annotations=annotations,
                                hierarchy_level=self.hierarchy_level)
        else:
            raise TypeError("line indices must be integers")

    def __extract_annotations_by_slice(self, start: int, stop: int) -> List[Annotation]:
        """
        extract annotations for given slice
        """
        assert start >= 0
        assert stop >= 0
        annotations = []
        for annotation in self.annotations:
            if start < annotation.end and stop > annotation.start:
                annotations.append(Annotation(
                    start=max(annotation.start, start) - start,
                    end=min(annotation.end, stop) - start,
                    name=annotation.name,
                    value=annotation.value))
        return annotations

    @property
    def line(self) -> str:
        return self._line

    @property
    def hierarchy_level(self) -> HierarchyLevel:
        return self._hierarchy_level

    @property
    def metadata(self) -> ParagraphMetadata:
        return self._metadata

    @property
    def annotations(self) -> List[Annotation]:
        return self._annotations

    @property
    def uid(self) -> str:
        return self._uid

    def set_hierarchy_level(self, hierarchy_level: Optional[HierarchyLevel]) -> None:
        self.__check_hierarchy_level(hierarchy_level)
        self._hierarchy_level = hierarchy_level

    def set_line(self, line: str) -> None:
        self._line = line

    def __repr__(self) -> str:
        return "LineWithMeta({})".format(self.line[:65])

    def __add__(self, other: Union["LineWithMeta", str]) -> "LineWithMeta":
        assert isinstance(other, (LineWithMeta, str))
        if len(other) == 0:
            return self
        if isinstance(other, str):
            line = self.line + other
            return LineWithMeta(line=line,
                                hierarchy_level=self._hierarchy_level,
                                metadata=self._metadata,
                                annotations=self.annotations,
                                uid=self.uid)
        line = self.line + other.line
        shift = len(self)
        other_annotations = []
        for annotation in other.annotations:
            new_annotation = Annotation(start=annotation.start + shift,
                                        end=annotation.end + shift,
                                        name=annotation.name,
                                        value=annotation.value)
            other_annotations.append(new_annotation)
        annotations = AnnotationMerger().merge_annotations(self.annotations + other_annotations, text=line)
        return LineWithMeta(line=line,
                            hierarchy_level=self._hierarchy_level,
                            metadata=self._metadata,
                            annotations=annotations,
                            uid=self.uid)
