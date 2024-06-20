import json
import os
import unittest

from dedoc.config import get_config
from train_dataset.extractors.line_with_label_extractor import LoadGTLineWithLabel


class TestLineWithMetaExtractor(unittest.TestCase):

    def test_txt_file(self) -> None:
        config = get_config()
        config["labeling_mode"] = True
        documents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "laws"))
        path = os.path.join(documents_path, "law_classifier_000000_Bhw.json")
        self.assertTrue(os.path.isfile(path))
        extractor = LoadGTLineWithLabel(labels_path=path, documents_path=documents_path, logfile_dir=config["path_debug"])
        lines = extractor.load_gt()
        with open(path) as file:
            labels = json.load(file)
            labels = {key: value for key, value in labels.items()}

        uids_set_real = {line.uid for line in lines[0]}
        uids2label = {item["data"]["_uid"]: item["labeled"][0] for item in labels.values()}
        self.assertSetEqual(set(uids2label.keys()), uids_set_real)
        for line in lines[0]:
            self.assertEqual(line.label, uids2label[line.uid])
