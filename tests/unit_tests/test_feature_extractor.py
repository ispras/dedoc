import unittest
from typing import List
import numpy as np

from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures


class TestRegexpFeatures(unittest.TestCase):
    feature_extractor = LawTextFeatures()
    result_matrix = np.array([[1, 0, 0], [0, 1, 1], [0, 0, 1]])

    def compare_with_expected(self, expected_matrix: List[List[int]], result: np.ndarray) -> None:
        self.assertEqual(len(expected_matrix), result.shape[0])
        self.assertEqual(len(expected_matrix[0]), result.shape[1])
        for row_res, row_exp in zip(result, expected_matrix):
            row_res = list(row_res)
            self.assertListEqual(row_exp, row_res)

    def test_prev_line_features(self) -> None:
        expected_matrix = [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 1],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 1)
        self.compare_with_expected(expected_matrix, result)

    def test_prev_line_features_2(self) -> None:
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [1, 0, 0],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 2)
        self.compare_with_expected(expected_matrix, result)

    def test_prev_line_features_3(self) -> None:
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 3)
        self.compare_with_expected(expected_matrix, result)

    def test_prev_line_features_4(self) -> None:
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._prev_line_features(self.result_matrix, 4)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features(self) -> None:
        expected_matrix = [
            [0, 1, 1],
            [0, 0, 1],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 1)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features_2(self) -> None:
        expected_matrix = [
            [0, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 2)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features_3(self) -> None:
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 3)
        self.compare_with_expected(expected_matrix, result)

    def test_next_line_features_4(self) -> None:
        expected_matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        result = AbstractFeatureExtractor._next_line_features(self.result_matrix, 4)
        self.compare_with_expected(expected_matrix, result)

    def test_previous_element_single(self) -> None:
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2", prev_item="1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.", prev_item="1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.", prev_item="1."))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="1.", prev_item="2"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="1", prev_item="3."))
        self.assertFalse(AbstractFeatureExtractor._can_be_prev_element(this_item="3.", prev_item="1."))
        self.assertFalse(AbstractFeatureExtractor._can_be_prev_element(this_item="3.", prev_item="5."))

    def test_previous_element_multiple(self) -> None:
        self.assertFalse(AbstractFeatureExtractor._can_be_prev_element(this_item="2.1.2", prev_item="2.1."))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.1.2", prev_item="2.1.1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.1.1", prev_item="2.1"))
        self.assertTrue(AbstractFeatureExtractor._can_be_prev_element(this_item="2.2", prev_item="2.1"))
