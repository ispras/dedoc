from typing import Tuple
import cv2
import numpy as np


# https://stackoverflow.com/questions/56905592/
class AdaptiveBinarizer:
    def __init__(self, block_size: int = 40, delta: int = 40) -> None:
        self.block_size = block_size
        self.delta = delta

    def binarize(self, img: np.ndarray) -> np.ndarray:
        img = self.__adjust_gamma(img)
        mask = self.__get_mask(img)
        image_in = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_out = self.__combine_block_image_process(image_in, mask)
        image_out = cv2.cvtColor(image_out, cv2.COLOR_GRAY2RGB)
        return image_out

    def __adjust_gamma(self, image: np.ndarray, gamma: float = 1.2) -> np.ndarray:
        # build a lookup table mapping the pixel values [0, 255] to
        # their adjusted gamma values
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")

        # apply gamma correction using the lookup table
        return cv2.LUT(image, table)

    def __preprocess(self, image: np.ndarray) -> np.ndarray:
        image = cv2.medianBlur(image, 3)
        return 255 - image

    def __postprocess(self, image: np.ndarray) -> np.ndarray:
        kernel = np.ones((3, 3), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return image

    def __get_block_index(self, image_shape: Tuple[int, int], yx: Tuple[int, int]) -> np.ndarray:
        y = np.arange(max(0, yx[0] - self.block_size), min(image_shape[0], yx[0] + self.block_size))
        x = np.arange(max(0, yx[1] - self.block_size), min(image_shape[1], yx[1] + self.block_size))
        return np.meshgrid(y, x)

    def _adaptive_median_threshold(self, img_in: np.ndarray) -> np.ndarray:
        med = np.median(img_in)
        img_out = np.zeros_like(img_in)
        img_out[img_in - med < self.delta] = 255
        kernel = np.ones((3, 3), np.uint8)
        img_out = 255 - cv2.dilate(255 - img_out, kernel, iterations=2)
        return img_out

    def __block_image_process(self, image: np.ndarray) -> np.ndarray:
        out_image = np.zeros_like(image)
        for row in range(0, image.shape[0], self.block_size):
            for col in range(0, image.shape[1], self.block_size):
                idx = (row, col)
                block_idx = self.__get_block_index(image.shape, idx)
                out_image[tuple(block_idx)] = self._adaptive_median_threshold(image[tuple(block_idx)])
        return out_image

    def __get_mask(self, img: np.ndarray) -> np.ndarray:
        image_in = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_in = self.__preprocess(image_in)
        image_out = self.__block_image_process(image_in)
        image_out = self.__postprocess(image_out)
        return image_out

    def _sigmoid(self, x: np.ndarray, orig: np.ndarray, rad: float) -> np.ndarray:
        k = np.exp((x - orig) * 5 / rad)
        return k / (k + 1.)

    def _combine_block(self, img_in: np.ndarray, mask: np.ndarray) -> np.ndarray:
        # First, we pre-fill the masked region of img_out to white
        # (i.e. background). The mask is retrieved from previous section.
        img_out = np.zeros_like(img_in)
        img_out[mask == 255] = 255
        fig_in = img_in.astype(np.float32)

        # Then, we store the foreground (letters written with ink)
        # in the `idx` array. If there are none (i.e. just background),
        # we move on to the next block.
        idx = np.where(mask == 0)
        if idx[0].shape[0] == 0:
            img_out[idx] = img_in[idx]
            return img_out

        # We find the intensity range of our pixels in this local part
        # and clip the image block to that range, locally.
        lo = fig_in[idx].min()
        hi = fig_in[idx].max()
        v = fig_in[idx] - lo
        r = hi - lo

        # Now we use good old OTSU binarization to get a rough estimation
        # of foreground and background regions.
        img_in_idx = img_in[idx]
        ret3, th3 = cv2.threshold(img_in[idx], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        if np.alltrue(th3[:, 0] != 255):
            img_out[idx] = img_in[idx]
            return img_out

        # Then we normalize the stuffs and apply sigmoid to gradually
        # combine the stuffs.
        bound_value = np.min(img_in_idx[th3[:, 0] == 255])
        bound_value = (bound_value - lo) / (r + 1e-5)
        f = (v / (r + 1e-5))
        f = self._sigmoid(f, bound_value + 0.05, 0.2)

        # Finally, we re-normalize the result to the range [0..255]
        img_out[idx] = (255. * f).astype(np.uint8)
        return img_out

    def __combine_block_image_process(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        out_image = np.zeros_like(image)

        for row in range(0, image.shape[0], self.block_size):
            for col in range(0, image.shape[1], self.block_size):
                block_idx = self.__get_block_index(image.shape, (row, col))
                out_image[tuple(block_idx)] = self._combine_block(image[tuple(block_idx)], mask[tuple(block_idx)])

        return out_image
