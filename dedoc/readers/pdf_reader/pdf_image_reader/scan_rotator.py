import logging
from typing import List, Iterator
import cv2
import numpy as np
from joblib import Parallel, delayed

from dedoc.utils.image_utils import rotate_image
from dedoc.utils.utils import get_batch


class ScanRotator:
    """
    Class corrects document's skew.
    """
    def __init__(self, *, config: dict) -> None:
        self.delta = 1  # step
        self.limit = 45  # max angle
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def determine_score(self, arr: np.ndarray, angle: int) -> (np.ndarray, float):
        data = rotate_image(arr, angle)
        histogram = np.sum(data, axis=1, dtype=float)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return score

    def auto_rotate(self, image: np.ndarray, orientation_angle: int = 0) -> (np.ndarray, int):
        if orientation_angle:
            image = rotate_image(image, orientation_angle)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        angles = np.arange(-self.limit, self.limit + self.delta, self.delta)
        scores = [self.determine_score(thresh, angle) for angle in angles]

        max_idx = scores.index(max(scores))
        if max_idx >= 2 and scores[max_idx - 2] > scores[max_idx] * 0.98:
            # if there are 2 approximately equal scores +- 1 step by max_score it will utilize angle between them
            best_angle = angles[max_idx - 1]
        elif max_idx < len(scores) - 2 and scores[max_idx + 2] > scores[max_idx] * 0.98:
            best_angle = angles[max_idx + 1]
        else:
            best_angle = angles[scores.index(max(scores))]

        rotated = rotate_image(image, best_angle)
        if self.config.get("debug_mode"):
            self.logger.debug(f'Best angle: {best_angle}, orientation angle: {orientation_angle}')
        return rotated, best_angle + orientation_angle

    def rotate(self, images: List[np.ndarray]) -> Iterator[np.ndarray]:
        """
        automatic rotation of list of images
        """
        n_jobs = self.config["n_jobs"]
        for batch in get_batch(size=n_jobs, iterable=images):
            rotated_ = Parallel(n_jobs=n_jobs)(delayed(self.auto_rotate)(img) for img in batch)
            for res, angle in rotated_:
                yield res
