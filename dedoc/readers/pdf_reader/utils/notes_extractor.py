import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Tuple

from dedocutils.data_structures import BBox
from pypdf import PdfReader
from rtree import Index, index

from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.linked_text_annotation import LinkedTextAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta


@dataclass
class PdfNote:
    type: Optional[str]  # noqa
    text: str
    bbox: BBox
    bbox_dict: dict[str, float]
    bbox_tuple: Tuple[float, float, float, float]

    def __init__(self, type_: str, text: str, author: str, bbox: BBox, height: int, width: int) -> None:
        if type_ == "/Text":
            # bottom left corner for popup-notes
            self.bbox = BBox(bbox.x_top_left, bbox.y_bottom_right - 1, 1, 1)
        elif type_ == "/Highlight":
            # bottom right corner for highlighted notes
            self.bbox = BBox(bbox.x_bottom_right - 1, bbox.y_bottom_right - 1, 1, 1)
        else:
            self.bbox = bbox

        self.bbox_dict = self.bbox.to_relative_dict(page_width=width, page_height=height)
        self.bbox_tuple = _bbox2tuple(self.bbox_dict)
        self.type = type_
        self.text = f"{author}: {text}" if author else text


@dataclass
class WordInfo:
    bbox_tuple: Tuple[float, float, float, float]
    start: int
    end: int


@dataclass
class LineInfo:
    line: LineWithMeta
    bbox_tuple: Tuple[float, float, float, float]
    words: List[WordInfo]
    words_idx: Optional[Index] = None


class PdfNotesExtractor:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def extract(self, path: str, lines: List[LineWithMeta]) -> None:
        page2notes = defaultdict(list)

        with open(path, "rb") as f:
            reader = PdfReader(f)

            for page in reader.pages:
                page_num = page.page_number
                try:
                    w, h = page["/CropBox"][2], page["/CropBox"][3]
                except Exception as e:
                    self.logger.warning(f"Failed to extract page {page_num} size: {e}")
                    continue

                for annot in page.get("/Annots", []):
                    obj = annot.get_object()
                    contents = obj.get("/Contents")
                    if not contents:
                        continue

                    coords = obj["/Rect"]
                    note = PdfNote(
                        type_=obj.get("/Subtype"),
                        text=contents,
                        author=obj.get("/T"),
                        bbox=BBox.from_two_points((int(coords[0]), int(h - coords[3])), (int(coords[2]), int(h - coords[1]))),
                        width=w,
                        height=h
                    )
                    page2notes[page_num].append(note)

        self.__process_lines(lines, page2notes)

    def __process_lines(self, lines: List[LineWithMeta], page2notes: dict[int, List[PdfNote]]) -> None:
        page2lines = defaultdict(list)
        for line in lines:
            page2lines[line.metadata.page_id].append(line)

        for page_num, page_notes in page2notes.items():
            page_lines = page2lines.get(page_num, [])
            if not page_lines:
                self.logger.warning(f"No lines on page {page_num} - skip notes extraction")
                continue

            lines_idx = index.Index()
            lines_info = []
            for page_line in page_lines:
                words = [
                    WordInfo(bbox_tuple=_bbox2tuple(json.loads(ann.value)), start=ann.start, end=ann.end)
                    for ann in page_line.annotations if ann.name == BBoxAnnotation.name
                ]
                if not words:
                    continue

                line_info = LineInfo(line=page_line, words=words, bbox_tuple=_line_bbox(words=words))
                lines_idx.insert(len(lines_info), line_info.bbox_tuple)
                lines_info.append(line_info)

            for note in page_notes:
                closest_line = next((lines_info[i] for i in lines_idx.nearest(note.bbox_tuple, 1)), None)
                if not closest_line:
                    self.logger.warning(f"No line was found for the note `{note.text}` on page `{page_num}`")
                    continue

                start, end = self.__get_annotation_coordinates(line_info=closest_line, note=note)
                closest_line.line.annotations.append(LinkedTextAnnotation(start=start, end=end, value=note.text))

    def __get_annotation_coordinates(self, line_info: LineInfo, note: PdfNote) -> Tuple[int, int]:
        # line y_bottom_right < note y_top_left
        if note.type == "/FreeText" and line_info.bbox_tuple[3] < note.bbox_tuple[1]:
            # note on the next line
            return 0, len(line_info.line.line) - 1

        if line_info.words_idx is None:
            words_idx = index.Index()
            for i, word in enumerate(line_info.words):
                words_idx.insert(i, word.bbox_tuple)
            line_info.words_idx = words_idx
        else:
            words_idx = line_info.words_idx

        closest_word = next((line_info.words[i] for i in words_idx.nearest(note.bbox_tuple, 1)), None)
        if not closest_word:
            self.logger.warning(f"No word was found for the note `{note.text}`, use the whole line")
            return 0, len(line_info.line.line) - 1

        return closest_word.start, closest_word.end


def _bbox2tuple(bbox: dict[str, float]) -> Tuple[float, float, float, float]:
    return bbox["x_top_left"], bbox["y_top_left"], bbox["x_top_left"] + bbox["width"], bbox["y_top_left"] + bbox["height"]


def _line_bbox(words: list[WordInfo]) -> Tuple[float, float, float, float]:
    x_top_left = min(word.bbox_tuple[0] for word in words)
    y_top_left = min(word.bbox_tuple[1] for word in words)
    x_bottom_right = max(word.bbox_tuple[2] for word in words)
    y_bottom_right = max(word.bbox_tuple[3] for word in words)
    return x_top_left, y_top_left, x_bottom_right, y_bottom_right
