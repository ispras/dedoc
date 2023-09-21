import os

import cv2
import numpy as np

from dedoc.config import get_config
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer


if __name__ == "__main__":
    config = get_config()
    output_folder = os.path.join(config.get("path_debug"), "debug_tables", "draw_results")
    os.makedirs(output_folder, exist_ok=True)
    root_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.abspath(os.path.join(root_dir, "..", "..", "tests", "data", "tables"))

    table_recognizer = TableRecognizer(config=get_config())

    for filename in os.listdir(input_folder):
        if os.path.splitext(filename)[-1] not in [".png", ".jpg"]:
            continue

        image = cv2.imread(os.path.join(input_folder, filename))
        color_backgr = np.max(image)
        padding = 40
        image_bigger = np.full((image.shape[0] + padding * 2, image.shape[1] + padding * 2, image.shape[2]), color_backgr)
        image_bigger[padding:-padding, padding:-padding] = image

        clean_image, tables = table_recognizer.recognize_tables_from_image(
            image=cv2.cvtColor(image_bigger, cv2.COLOR_BGR2GRAY),
            page_number=0,
            language="rus+eng",
            orient_analysis_cells=False,
            orient_cell_angle=0,
            table_type=""
        )

        for table in tables:
            white_rect = np.ones(image_bigger.shape, dtype=np.uint8) * 255

            for row in table.matrix_cells:
                for cell in row:
                    box = [cell.x_top_left, cell.y_top_left, cell.x_bottom_right, cell.y_bottom_right]
                    color = (np.random.random_sample(3) * 255).astype(np.uint8).tolist()
                    cv2.rectangle(white_rect, (box[0], box[1]), (box[2], box[3]), color=color, thickness=-1)

            res = cv2.addWeighted(image_bigger, 0.7, white_rect, 0.3, 1.0)
            cv2.imwrite(os.path.join(output_folder, filename), res)
            print(f"Write {filename}")

