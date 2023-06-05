import logging
from collections import namedtuple
from typing import List
import cv2

from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_cell_extractor import OCRCellExtractor

logger = logging.getLogger("TableRecognizer.TableTree")

'''-------------------------------Таблица в виде дерева, полученная от OpenCV----------------------------------------'''
ContourCell = namedtuple("ContourCell", ["id_con", "image"])


class TableTree(object):
    """
    Table which has cells as sorted childs of tree.
    Table has type of tree and was obtained with help contour analysis.
    """

    def __init__(self, *, config: dict) -> None:
        self.left = None
        self.right = None
        self.data_bb = None  # [x_begin, y_begin, width, height]
        self.id_contours = None
        self.parent = None
        self.children = []  # table cells
        self.text = ""
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    @staticmethod
    def set_text_into_tree(tree: "TableTree",
                           cell_images: List[ContourCell],
                           cur_depth: int,
                           begin_depth: int,
                           end_depth: int,
                           language: str = "rus",
                           orient_analysis_cells: bool = False,
                           *,
                           config: dict) -> None:

        stack = [(tree, cur_depth, begin_depth, end_depth)]
        trees = []
        while len(stack) > 0:
            tree, cur_depth, begin_depth, end_depth = stack.pop()
            if begin_depth <= cur_depth <= end_depth:
                img_cell = [pair.image for i, pair in enumerate(cell_images) if pair.id_con == tree.id_contours][0]
                trees.append((tree, img_cell))
                if tree.config.get("debug_mode", False):
                    config.get("logger", logging.getLogger()).debug("{} : text : {}".format(tree.id_contours, tree.text))
            for ch in tree.children:
                stack.append((ch, cur_depth + 1, begin_depth, end_depth))
        # texts = [get_cell_text_by_ocr(image, language=language) for _, image in trees]
        images = [image for _, image in trees]
        cell_extractor = OCRCellExtractor(config=config)
        if orient_analysis_cells:
            texts = cell_extractor.get_cells_rotated(img_cells=images, language=language)
        else:
            texts = cell_extractor.get_cells_text(img_cells=images, language=language)
        assert len(trees) == len(texts)
        for text, (tree, img_cell) in zip(texts, trees):
            tree.text = text

    @staticmethod
    def parse_contours_to_tree(contours: List, hierarchy: List, *, config: dict) -> "TableTree":
        table_tree = TableTree(config=config)
        table_tree.id_contours = 0
        if len(contours) == 0:
            return table_tree

        bounding_box = [cv2.boundingRect(c) for c in contours[0]]
        table_tree.data_bb = bounding_box[0]

        table_tree = table_tree.__build_childs(table_tree, hierarchy, contours)
        return table_tree

    def print_tree(self, depth: int) -> None:
        if not self.data_bb or not self.id_contours:
            return

        indent = ''.join(['\t' for _ in range(depth)])
        self.logger.debug("{}{} : coord: {}, {}, {}, {}".format(indent,
                                                                self.id_contours,
                                                                self.data_bb[0],
                                                                self.data_bb[1],
                                                                self.data_bb[0] + self.data_bb[2],
                                                                self.data_bb[1] + self.data_bb[3]))
        for ch in self.children:
            ch.print_tree(depth + 1)

    def __build_childs(self, cur: "TableTree", hierarchy: List, contours: List) -> "TableTree":
        list_childs = []
        for i, h in enumerate(hierarchy[0]):
            if h[3] == cur.id_contours:
                bounding_box = cv2.boundingRect(contours[i])  # [x_begin, y_begin, width, height]
                # Эвристика №1 на ячейку
                if bounding_box[2] < self.config["min_w_cell"] or bounding_box[3] < self.config["min_h_cell"]:
                    if self.config.get("debug_mode", False):
                        self.logger.debug("Contour {} isn't correct".format(i))
                    continue
                t = TableTree(config=self.config)
                t.id_contours = i
                t.data_bb = bounding_box
                t.parent = cur
                list_childs.append(t)
                if h[2] != -1:
                    t = TableTree(config=self.config).__build_childs(t, hierarchy, contours)
                cur.__add_child(t)
        cur.children = sorted(cur.children, key=lambda ch: (ch.data_bb[1], ch.data_bb[0]), reverse=False)
        return cur

    def __add_child(self, child_tree: "TableTree") -> None:
        self.children.append(child_tree)
