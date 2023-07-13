import numpy as np
from scipy.stats import norm
from sklearn.cluster import AgglomerativeClustering


class BoldAgglomerativeClusterizer:
    def __init__(self) -> None:
        self.significance_level = 0.2

    def clusterize(self, x: np.ndarray) -> np.ndarray:
        x_vectors = self.__get_prop_vectors(x)
        x_clusters = self.__get_clusters(x_vectors)
        x_indicator = self.__get_indicator(x, x_clusters)
        return x_indicator

    def __get_prop_vectors(self, x: np.ndarray) -> np.ndarray:
        nearby_x = x.copy()
        nearby_x[:-1] += x[1:]
        nearby_x[1:] += x[:-1]
        nearby_x[0] += x[0]
        nearby_x[-1] += x[-1]
        nearby_x = nearby_x / 3.
        return np.stack((x, nearby_x), 1)

    def __get_clusters(self, x_vectors: np.ndarray) -> np.ndarray:
        agg = AgglomerativeClustering()
        agg.fit(x_vectors)
        x_clusters = agg.labels_
        return x_clusters

    def __get_indicator(self, x: np.ndarray, x_clusters: np.ndarray) -> np.ndarray:
        # https://www.tsi.lv/sites/default/files/editor/science/Research_journals/Tr_Tel/2003/V1/yatskiv_gousarova.pdf
        # https://www.svms.org/classification/DuHS95.pdf
        # Pattern Classification and Scene Analysis (2nd ed.)
        # Part 1: Pattern Classification
        # Richard O. Duda, Peter E. Hart and David G. Stork
        # February 27, 1995
        f1 = self.__get_f1_homogeneous(x, x_clusters)
        f_cr = self.__get_f_criterion_homogeneous(n=len(x))

        if f_cr < f1:
            return np.zeros_like(x)
        if np.mean(x[x_clusters == 1]) < np.mean(x[x_clusters == 0]):
            x_clusters[x_clusters == 1] = 1.0
            x_clusters[x_clusters == 0] = 0.0
        else:
            x_clusters[x_clusters == 0] = 1.0
            x_clusters[x_clusters == 1] = 0.0

        return x_clusters

    def __get_f1_homogeneous(self, x: np.ndarray, x_clusters: np.ndarray) -> float:
        x_clust0 = x[x_clusters == 0]
        x_clust1 = x[x_clusters == 1]
        if len(x_clust0) == 0 or len(x_clust1) == 0:
            return 1

        w1 = np.std(x) * len(x)
        w2 = np.std(x_clust0) * len(x_clust0) + np.std(x_clust1) * len(x_clust1)
        f1 = w2 / w1
        return f1

    def __get_f_criterion_homogeneous(self, n: int, p: int = 2) -> float:
        za1 = norm.ppf(1 - self.significance_level, loc=0, scale=1)
        f_cr = 1 - 2 / (np.pi * p) - za1 * np.sqrt(2 * (1 - 8 / (np.pi ** 2 * p)) / (n * p))
        return f_cr
