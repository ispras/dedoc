import csv
import json
import os
from typing import List, Tuple

import cv2

from dedoc.config import get_config
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader


def _create_cell(c: str, text_cells: list) -> Cell:
    cell = Cell(x_bottom_right=-1, x_top_left=-1, y_top_left=-1, y_bottom_right=-1)
    if "a" in c:
        cell.is_attribute = True
    # loading cell text
    if len(text_cells) != 0:
        cell_text = [r for r in text_cells if r[0] == c]
        if len(cell_text) != 0:
            cell.text = cell_text[0][-1]
    return cell


def load_from_csv(path_csv: str, path_class_2_csv: str = "") -> List[List[Cell]]:
    text_cells = []
    if path_class_2_csv != "":
        csv_file_class_2 = open(path_class_2_csv, "r", newline="")
        reader_class_2 = csv.reader(csv_file_class_2)
        text_cells = [r for r in reader_class_2]

    matrix = []
    with open(path_csv, "r", newline="") as csv_file:
        reader = csv.reader(csv_file)

        for raw in reader:
            if len(raw) >= 5 and raw[0] == "bbox":
                pass
            else:
                line = [_create_cell(c, text_cells) for c in raw if c != ""]
                if len(line) != 0:
                    matrix.append(line)
    return matrix


def get_quantitative_parameters(matrix: List[List[Cell]]) -> Tuple[int, int, int, int]:
    cnt_a_cell, cnt_cell, cnt_columns, cnt_rows = 0, 0, 0, 0

    # calculating data
    if len(matrix) > 0:
        cnt_columns = len(matrix[0])
    cnt_rows = len(matrix)

    for i in range(0, len(matrix)):
        for j in range(0, len(matrix[i])):
            if matrix[i][j].is_attribute:
                cnt_a_cell += 1

            cnt_cell += 1

    return cnt_a_cell, cnt_cell, cnt_columns, cnt_rows


def calc_agreement(matrix_gt: List[List[Cell]], matrix: List[List[Cell]]) -> float:
    q_params = get_quantitative_parameters(matrix)
    q_params_gt = get_quantitative_parameters(matrix_gt)

    equal_indexes = [i for i in range(0, len(q_params)) if q_params[i] == q_params_gt[i]]

    agreement = 1.0 * len(equal_indexes) / len(q_params_gt)
    return agreement


def draw_recognized_cell(tables: List[ScanTable], path_image: str, path_save: str) -> None:
    img = cv2.imread(path_image)
    for t_index in range(0, len(tables)):
        table = tables[t_index].matrix_cells
        bbox = tables[t_index].locations.location
        blue_color, green_color, red_color = (255, 0, 0), (0, 255, 0), (0, 0, 255)
        cv2.rectangle(img, (bbox.x_top_left, bbox.y_top_left), (bbox.width, bbox.height), blue_color, 6)
        for i in range(0, len(table)):
            for j in range(0, len(table[i])):
                cv2.rectangle(img, (table[i][j].x_top_left, table[i][j].y_top_left), (table[i][j].x_bottom_right, table[i][j].y_bottom_right), red_color, 4)
                cv2.putText(img, str(table[i][j].id_con), (table[i][j].x_top_left, table[i][j].y_bottom_right), cv2.FONT_HERSHEY_PLAIN, 4, green_color)
    cv2.imwrite(path_save, img)


def save_json(tables: List[ScanTable], number_test_string: str, path_output: str) -> None:
    for i in range(0, len(tables)):
        with open(f"{path_output}{number_test_string}_table_{i}.json", "w") as out:
            json.dump(tables[i].to_dict(), out, ensure_ascii=False, indent=2)


def calc_accuracy(path_image: str, path_gt_struct: str, path_gt_text: str, path_save_image: str, path_save_json: str) -> None:
    from os import listdir
    from os.path import isfile, join

    os.makedirs(path_save_image, exist_ok=True)
    os.makedirs(path_save_json, exist_ok=True)

    image_files = [f for f in listdir(path_image) if isfile(join(path_image, f))]
    agreements = []

    for image_file in image_files:
        name_example = image_file.split(".")[0].split("_")[0]
        # predict tables
        image = cv2.imread(path_image + image_file, 0)
        # TODO fix this
        clean_images, tables = PdfImageReader(config=get_config()).get_tables([image])
        draw_recognized_cell(tables, path_image + image_file, path_save_image + image_file)
        save_json(tables, name_example, path_save_json)

        gt_files = [f for f in listdir(path_gt_struct) if isfile(join(path_gt_struct, f)) and name_example + "_" in f]
        for index_table in range(0, len(gt_files)):

            csv_filename = path_gt_struct + name_example + "_" + str(index_table + 1) + ".csv"
            csv_text_filename = path_gt_text + name_example + "_" + str(index_table + 1) + "_text.csv"
            if os.path.exists(csv_filename):
                if not os.path.exists(csv_text_filename):
                    csv_text_filename = ""
                # load_GT
                matrix_cell_gt = load_from_csv(csv_filename, csv_text_filename)
                # calc agreement
                if len(tables) == 0 and matrix_cell_gt == []:
                    agreements.append(1.0)
                elif len(tables) <= index_table:
                    agreements.append(0)
                else:
                    agreement = calc_agreement(matrix_cell_gt, tables[index_table].matrix_cells)
                    agreements.append(agreement)


if __name__ == "__main__":
    current_path = os.path.dirname(__file__) + "/"
    calc_accuracy(current_path + "../../backend/test_dataset_table/images/",
                  current_path + "../../backend/test_dataset_table/GT_struct/",
                  current_path + "../../backend/test_dataset_table/GT_text/",
                  "/tmp/backend_claw/out_tables/acc/draw_tables/",
                  "/tmp/backend_claw/out_tables/acc/json_tables/")
