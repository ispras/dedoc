from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument


class AbstractStructureExtractor(ABC):
    """
    This class adds additional information to the given unstructured document (list of lines).
    Types of lines and their levels in the document are added
    """

    @abstractmethod
    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        """
        Take as an input the document from some reader, finds lines types and their hierarchy levels and adds them
        """
        pass

    def _postprocess(self, lines: List[LineWithMeta], paragraph_type: List[str], regexps: List,
                     excluding_regexps: List) -> List[LineWithMeta]:
        """
        The function searches for which of regular expressions (for regexps parameters) the string matches.
        If there is match, then additional node is creating.
        To filter out garbage (extra letters, spaces, etc.),
        the excluding_regexps is applied after for the matched substring (for example: "1.П"->"1.", "4.7.\t"->"4.7.")
        :param lines: input line
        :param paragraph_type: list of paragraph type
        :param regexps: list of regular pattern according to list of paragraph_type
        :param excluding_regexps: list of filtering garbage regular pattern according to list of paragraph_type
        :return: new post-processed LineWithMetas
        """
        result = []
        for line in lines:
            if line.hierarchy_level.is_raw_text() and len(line.line) == 0:  # skip empty raw text
                continue
            if line.hierarchy_level.paragraph_type in paragraph_type:
                matched = False
                for num, regexp in enumerate(regexps):
                    match = regexp.match(line.line)

                    if match:
                        matched = True
                        start = match.start()
                        end = match.end()
                        if excluding_regexps[num]:
                            match_excluding = excluding_regexps[num].search(line.line[start:end])
                            end = match_excluding.start() if match_excluding else end

                        result.append(LineWithMeta(line=line.line[start: end],
                                                   hierarchy_level=line.hierarchy_level,
                                                   metadata=line.metadata,
                                                   annotations=self._select_annotations(line.annotations, start, end),
                                                   uid=line.uid))
                        metadata = deepcopy(line.metadata)
                        metadata.predicted_classes = None
                        metadata.paragraph_type = "raw_text"

                        rest_text = line.line[end:]
                        if len(rest_text) > 0:
                            annotations = self._select_annotations(line.annotations, end, len(line.line))
                            result.append(LineWithMeta(line=rest_text,
                                                       hierarchy_level=HierarchyLevel.create_raw_text(),
                                                       metadata=metadata,
                                                       annotations=annotations,
                                                       uid=line.uid + "_split"))
                        break
                if not matched:
                    result.append(line)
            else:
                result.append(line)

        return result

    def _select_annotations(self, annotations: List[Annotation], start: int, end: int) -> List[Annotation]:
        assert start <= end
        res = []
        for annotation in annotations:
            if annotation.name in [TableAnnotation.name, AttachAnnotation.name]:
                if start == 0:
                    new_annotation = Annotation(start=start, end=end, value=annotation.value, name=annotation.name)
                    res.append(new_annotation)
            elif annotation.end > start and annotation.start <= end:
                new_start = max(annotation.start, start) - start
                new_end = min(annotation.end, end) - start
                new_annotation = Annotation(start=new_start, end=new_end, value=annotation.value, name=annotation.name)
                res.append(new_annotation)
        return res
