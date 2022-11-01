from typing import Tuple
import PIL
import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import maximum_filter

from src.readers.scanned_reader.data_classes.bbox import BBox


def get_bbox_from_image(image: Image, bbox: BBox, resize: Tuple[int, int] = (300, 15)) -> PIL:
    """
    take image and bbox and crop bbox from this image, resize it if necessary and return.
    @param image: pil image
    @param bbox: instance of class BBox - some part of image
    @param resize: often we need image of the same size, so we can resize cropped image. If None does not resize and
    return image as is
    @return: PIL image
    """
    rectangle = (bbox.x_top_left,
                 bbox.y_top_left,
                 bbox.x_bottom_right,
                 bbox.y_bottom_right
                 )
    if isinstance(image, np.ndarray):
        image = PIL.Image.fromarray(image)
    cropped = image.crop(rectangle)
    if resize is not None:
        cropped = cropped.resize((300, 15)).convert('RGB')
    return cropped


def rotate_image(image: np.ndarray, angle: float, color_bound: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """
    Rotates an image (angle in degrees) and expands image to avoid cropping
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

    rotated_mat = cv2.warpAffine(image, rotation_mat, (bound_w, bound_h),
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=color_bound)
    return rotated_mat


def crop_image_text(image: np.ndarray) -> np.ndarray:
    """
    crop image to take text area only (crop empty space)
    @param image: original image
    @return: cropped image
    """
    edges = cv2.Canny(image, 100, 200)
    edges = maximum_filter(edges, (10, 10))
    x_sum = np.arange(edges.shape[0])[edges.max(axis=1) > 0]
    y_sum = np.arange(edges.shape[1])[edges.max(axis=0) > 0]
    if x_sum.shape[0] > 0 and y_sum.shape[0] > 0:
        x_lower = max(0, x_sum.min() - 10)
        x_upper = min(image.shape[0], x_sum.max() + 10)
        y_lower = max(0, y_sum.min() - 10)
        y_upper = min(image.shape[1], y_sum.max() + 10)
        image_crop = image[x_lower: x_upper, y_lower: y_upper]
        assert y_lower <= y_upper
        assert x_lower <= x_upper
    else:
        image_crop = image
    return image_crop


supported_image_types = {"bmp",
                         "dib",
                         "eps",
                         "gif",
                         "hdr",
                         "jfif",
                         "jp2",
                         "jpe",
                         "jpeg",
                         "jpg",
                         "pbm",
                         "pcx",
                         "pgm",
                         "pic",
                         "png",
                         "pnm",
                         "ppm",
                         "ras",
                         "sgi",
                         "sr",
                         "tiff",
                         "webp",
                         "j2k"}
supported_image_types = {prefix + image_format for image_format in supported_image_types for prefix in [".", ""]}
