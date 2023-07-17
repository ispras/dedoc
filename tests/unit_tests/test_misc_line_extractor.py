import json
import os
import unittest

from tests.test_utils import get_test_config
from dedoc.train_dataset.extractors.line_with_meta_extractor import LineWithMetaExtractor


class TestLineWithMetaExtractor(unittest.TestCase):

    def test_txt_file(self) -> None:
        config = get_test_config()
        documents_path = os.path.join(os.path.dirname(__file__), "..", "data", "laws")
        documents_path = os.path.abspath(documents_path)
        self.assertTrue(os.path.isdir(documents_path))
        path = os.path.join(documents_path, "law_classifier_000000_Bhw.json")
        self.assertTrue(os.path.isfile(path))
        extractor = LineWithMetaExtractor(path=path, documents_path=documents_path, config=config)
        lines = extractor.create_task()
        with open(path) as file:
            labels = json.load(file)
            labels = {key: value for key, value in labels.items() if not value["data"]["_uid"].endswith("_split")}

        uids_set_real = {line.uid for line in lines}
        uids2label = {item["data"]["_uid"]: item["labeled"][0] for item in labels.values()}
        self.assertSetEqual(set(uids2label.keys()), uids_set_real)
        for line in lines:
            self.assertEqual(line.label, uids2label[line.uid])
