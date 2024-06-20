import cv2
import numpy as np


class ValleyEmphasisBinarizer:
    def __init__(self, n: int = 5) -> None:
        self.n = n

    def binarize(self, image: np.ndarray) -> np.ndarray:
        if image.shape[-1] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshold = self.__get_threshold(image)

        image[image <= threshold] = 0
        image[image > threshold] = 1
        return image

    def __get_threshold(self, gray_img: np.ndarray) -> int:
        c, x = np.histogram(gray_img, bins=255)
        h, w = gray_img.shape
        total = h * w

        sum_val = 0
        for t in range(255):
            sum_val = sum_val + (t * c[t] / total)

        var_max = 0
        threshold = 0

        omega_1 = 0
        mu_k = 0

        for t in range(254):
            omega_1 = omega_1 + c[t] / total
            omega_2 = 1 - omega_1
            mu_k = mu_k + t * (c[t] / total)
            mu_1 = mu_k / omega_1 if omega_1 != 0. else 0.
            mu_2 = (sum_val - mu_k) / omega_2 if omega_2 != 0. else 0.
            sum_of_neighbors = np.sum(c[max(1, t - self.n):min(255, t + self.n)])
            denom = total
            current_var = (1 - sum_of_neighbors / denom) * (omega_1 * mu_1 ** 2 + omega_2 * mu_2 ** 2)

            if current_var > var_max:
                var_max = current_var
                threshold = t

        return threshold
