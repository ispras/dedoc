from copy import deepcopy
from typing import List, Tuple

import PIL
import cv2
import numpy as np
from PIL import Image, ImageDraw
from dedocutils.data_structures import BBox
from scipy.ndimage import maximum_filter


def get_highest_pixel_frequency(image: np.ndarray) -> int:
    unique, counts = np.unique(image.reshape(-1, 1), axis=0, return_counts=True)
    color = unique[np.argmax(counts)][0]
    if color == 0:
        color = np.uint8(255)

    return color


def get_bbox_from_image(image: Image, bbox: BBox, resize: Tuple[int, int] = (300, 15)) -> PIL:
    """
    take image and bbox and crop bbox from this image, resize it if necessary and return.
    @param image: pil image
    @param bbox: instance of class BBox - some part of image
    @param resize: often we need image of the same size, so we can resize cropped image. If None does not resize and
    return image as is
    @return: PIL image
    """
    rectangle = (bbox.x_top_left, bbox.y_top_left, bbox.x_bottom_right, bbox.y_bottom_right)
    if isinstance(image, np.ndarray):
        image = PIL.Image.fromarray(image)
    cropped = image.crop(rectangle)
    if resize is not None:
        cropped = cropped.resize((300, 15)).convert("RGB")
    return cropped


def rotate_image(image: np.ndarray, angle: float, color_bound: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """
    Rotates an image (angle in degrees) and expands image to avoid cropping (do bounds of color_bound)
    Changes width and height of image (image.shape != rotated_image.shape)
    """
    height, width = image.shape[:2]
    image_center = (width / 2, height / 2)
    rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)

    abs_cos = abs(rotation_mat[0, 0])
    abs_sin = abs(rotation_mat[0, 1])

    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    rotation_mat[0, 2] += bound_w / 2 - image_center[0]
    rotation_mat[1, 2] += bound_h / 2 - image_center[1]

    rotated_mat = cv2.warpAffine(image, rotation_mat, (bound_w, bound_h), borderMode=cv2.BORDER_CONSTANT, borderValue=color_bound)
    return rotated_mat


def crop_image_text(image: np.ndarray) -> BBox:
    """
    crop image to take text area only (crop empty space)
    @param image: original image
    @return: cropped image
    """
    im_height, im_width = image.shape[0], image.shape[1]
    edges = cv2.Canny(image, 100, 200)
    edges = maximum_filter(edges, (10, 10))
    y_sum = np.arange(edges.shape[0])[edges.max(axis=1) > 0]
    x_sum = np.arange(edges.shape[1])[edges.max(axis=0) > 0]
    if y_sum.shape[0] > 0 and x_sum.shape[0] > 0:
        y_top = max(0, y_sum.min() - 10)
        y_bottom = min(im_height, y_sum.max() + 10)
        x_top = max(0, x_sum.min() - 10)
        x_bottom = min(im_width, x_sum.max() + 10)
        return BBox(x_top, y_top, x_bottom - x_top, y_bottom - y_top)
    else:
        return BBox(x_top_left=0, y_top_left=0, width=im_width, height=im_height)


def draw_rectangle(image: PIL.Image, x_top_left: int, y_top_left: int, width: int, height: int, color: Tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
    if color == "black":
        color = (0, 0, 0)
    source_img = deepcopy(image).convert("RGBA")

    draw = ImageDraw.Draw(source_img)
    x_bottom_right = x_top_left + width + 5
    y_bottom_right = y_top_left + height + 5
    start_point = (x_top_left - 5, y_top_left - 5)
    end_point = (x_bottom_right, y_bottom_right)
    draw.rectangle((start_point, end_point), outline=color, width=5)

    return np.array(source_img)


def get_concat_v(images: List[Image.Image]) -> Image:
    if len(images) == 1:
        return images[0]
    width = max((image.width for image in images))
    height = sum((image.height for image in images))
    dst = Image.new("RGB", (width, height))
    height = 0
    for image in images:
        dst.paste(image, (0, height))
        height += image.height
    return dst
