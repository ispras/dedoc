import abc
from copy import deepcopy
from typing import List, Iterator

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_parser.hierarchy_level import HierarchyLevel


class AbstractLineTypeClassifier(abc.ABC):

    document_type = None

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.chunk_start_tags = ["header", "body"]
        self.hl_type = ""
        self._chunk_hl_builders = []

    @abc.abstractmethod
    def predict(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        """
        :param lines: image and bboxes with text, it is useful for feature extraction and label predictions
        :return: lines with metadata and predicted labels and hierarchy levels
        """
        pass

    def get_chunk_start_tags(self) -> List[str]:
        return self.chunk_start_tags

    def get_hl_type(self) -> str:
        return self.hl_type

    @staticmethod
    def _select_annotations(annotations: List[Annotation], start: int, end: int) -> List[Annotation]:
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

    def _line_postprocess(self,
                          lines: List[LineWithMeta],
                          paragraph_type: List[str],
                          regexps: List,
                          excluding_regexps: List) -> Iterator[LineWithMeta]:
        """
        The function searches for which of regular expressions (for regexps parameters) the string matches.
        If there is match, then additional node is creating.
        To filter out garbage (extra letters, spaces, etc.),
        the excluding_regexps is applied after for the matched substring (for example: "1.П"->"1.", "4.7.\t"->"4.7.")
        :param lines: input line
        :param paragraph_type: list of paragraph type
        :param regexps: list of regular pattern according to list of paragraph_type
        :param excluding_regexps: list of filtering grabage regular pattern according to list of paragraph_type
        :return: new post-processed LineWithMetas
        """
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

                        yield LineWithMeta(line=line.line[start: end],
                                           hierarchy_level=line.hierarchy_level,
                                           metadata=line.metadata,
                                           annotations=self._select_annotations(line.annotations, start, end),
                                           uid=line.uid
                                           )
                        metadata = deepcopy(line.metadata)
                        metadata.predicted_classes = None
                        metadata.paragraph_type = "raw_text"

                        rest_text = line.line[end:]
                        if len(rest_text) > 0:
                            annotations = self._select_annotations(line.annotations, end, len(line.line))
                            yield LineWithMeta(line=rest_text,
                                               hierarchy_level=HierarchyLevel.create_raw_text(),
                                               metadata=metadata,
                                               annotations=annotations,
                                               uid=line.uid + "_split")
                        break
                if not matched:
                    yield line
            else:
                yield line
