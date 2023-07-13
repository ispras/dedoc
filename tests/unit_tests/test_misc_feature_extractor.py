import unittest
from typing import List
import numpy as np

from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor


class TestRegexpFeatures(unittest.TestCase):
    """
    Class with implemented tests for feature extractor
    """
    result_matrix = np.array([[1, 0, 0], [0, 1, 1], [0, 0, 1]])

    def compare_with_expected(self, expected_matrix: List[List[int]], result: np.ndarray) -> None:
        """
        Method for comparison of two matrices
        """
        self.assertEqual(len(expected_matrix), result.shape[0])
        self.assertEqual(len(expected_matrix[0]), result.shape[1])
        for row_res, row_exp in zip(result, expected_matrix):
            row_res = list(row_res)
            self.assertListEqual(row_exp, row_res)

    def test_prev_line_features(self) -> None:
        """
        Tests shift on 1 line backward
        """
        expected_matrix = [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 1],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 1)
        self.compare_with_expected(expected_matrix, result)

    def test_prev_line_features_2(self) -> None:
        """
        Tests shift on 2 lines backward
        """
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [1, 0, 0],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 2)
        self.compare_with_expected(expected_matrix, result)

    def test_prev_line_features_3(self) -> None:
        """
        Tests shift on 3 lines backward
        """
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 3)
        self.compare_with_expected(expected_matrix, result)

    def test_prev_line_features_4(self) -> None:
        """
        Tests shift on 4 lines backward
        """
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 4)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features(self) -> None:
        """
        Tests shift on 1 line forward
        """
        expected_matrix = [
            [0, 1, 1],
            [0, 0, 1],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 1)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features_2(self) -> None:
        """
        Tests shift on 2 lines forward
        """
        expected_matrix = [
            [0, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 2)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features_3(self) -> None:
        """
        Tests shift on 3 lines forward
        """
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 3)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features_4(self) -> None:
        """
        Tests shift on 4 lines forward
        """
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 4)
        self.compare_with_expected(expected_matrix, result)

    def test_previous_element_single(self) -> None:
        """
        Tests if a single element can be a previous element for another single element
        """
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2", prev_item="1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.", prev_item="1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.", prev_item="1."))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="1.", prev_item="2"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="1", prev_item="3."))
        self.assertFalse(AbstractFeatureExtractor._can_be_prev_element(this_item="3.", prev_item="1."))
        self.assertFalse(AbstractFeatureExtractor._can_be_prev_element(this_item="3.", prev_item="5."))

    def test_previous_element_multiple(self) -> None:
        """
        Tests if a complex element can be a previous element for another complex element
        """
        self.assertFalse(AbstractFeatureExtractor._can_be_prev_element(this_item="2.1.2", prev_item="2.1."))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.1.2", prev_item="2.1.1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.1.1", prev_item="2.1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.2", prev_item="2.1"))
