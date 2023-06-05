import argparse
import glob
import os
import cv2
import numpy as np

from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--image", help="Path to checkpoint")
parser.add_argument("-f", "--input_folder", help="Path to input image")
parser.add_argument("-o", "--output_folder", help="Path to output image")

parser = parser.parse_args()

if __name__ == "__main__":

    if not os.path.exists(parser.output_folder):
        os.makedirs(parser.output_folder, exist_ok=True)

    path_to_img = [parser.image] if parser.image is not None else glob.glob("{}/*".format(parser.input_folder))

    for img_path in path_to_img:
        image = cv2.imread(img_path)
        color_backgr = np.max(image)
        padding = 40
        image_bigger = np.full((image.shape[0] + padding * 2,
                                image.shape[1] + padding * 2,
                                image.shape[2]), color_backgr)
        image_bigger[padding:-padding, padding:-padding] = image
        # TODO fix this
        clean_images, tables = PdfImageReader(config={}).get_tables([cv2.cvtColor(image_bigger, cv2.COLOR_BGR2GRAY)])
        for table in tables:

            white_rect = np.ones(image_bigger.shape, dtype=np.uint8) * 255
            for row in table.matrix_cells:
                for cell in row:
                    box = [cell.x_top_left, cell.y_top_left, cell.x_bottom_right, cell.y_bottom_right]
                    color = (np.random.random_sample(3) * 255).astype(np.uint8).tolist()
                    cv2.rectangle(white_rect, (box[0], box[1]), (box[2], box[3]), color=color, thickness=-1)

            res = cv2.addWeighted(image_bigger, 0.7, white_rect, 0.3, 1.0)

            if len(path_to_img) == 1:
                cv2.imwrite(parser.output_folder, res)
            else:
                cv2.imwrite("{}/{}".format(parser.output_folder, img_path.split('/')[-1]), res)
