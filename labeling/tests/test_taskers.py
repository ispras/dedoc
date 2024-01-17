import os
import tempfile
import unittest
from zipfile import ZipFile

from PIL import Image

from dedoc.config import get_config
from train_dataset.taskers.concrete_taskers.line_label_tasker import LineLabelTasker
from train_dataset.taskers.tasker import Tasker


class TestTaskers(unittest.TestCase):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "taskers"))
    path2lines = os.path.join(base_path, "lines.jsonlines")
    path2docs = os.path.join(base_path, "images")
    manifest_path = os.path.join(base_path, "test_manifest.md")
    config_path = os.path.join(base_path, "test_config.json")
    config = get_config()
    config["labeling_mode"] = True

    def test_paths(self) -> None:
        self.assertTrue(os.path.isfile(self.path2lines), self.path2lines)
        self.assertTrue(os.path.isfile(self.manifest_path), self.manifest_path)
        self.assertTrue(os.path.isfile(self.config_path), self.config_path)
        self.assertTrue(os.path.isdir(self.path2docs), self.path2docs)

    def test_line_label_tasker_size1(self) -> None:
        tasker = self._get_line_label_classifier()
        task_cnt = 0
        for task_path in tasker.create_tasks(task_size=10):
            task_cnt += 1
            self._test_task_archive(task_path)

    def test_line_label_tasker_size2(self) -> None:
        tasker = self._get_line_label_classifier()

        task_cnt = 0
        for task_path in tasker.create_tasks(task_size=2):
            task_cnt += 1
            self._test_task_archive(task_path)

    def test_tasker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            taskers = {
                "law_classifier": LineLabelTasker(
                    path2lines=self.path2lines,
                    path2docs=self.path2docs,
                    manifest_path=self.manifest_path,
                    config_path=self.config_path,
                    tmp_dir=tmpdir,
                    config=self.config
                )
            }
            tasker = Tasker(line_info_path=self.path2lines, images_path=self.path2docs, save_path=tmpdir, concrete_taskers=taskers, config=self.config)
            tasks_path, task_size = tasker.create_tasks(type_of_task="law_classifier", task_size=1)
            self.assertTrue(os.path.isfile(tasks_path))
            self.assertEqual(1, task_size)
            with ZipFile(tasks_path) as archive:
                self.assertIn("original_documents.zip", archive.namelist())

    def _get_line_label_classifier(self) -> LineLabelTasker:
        tasker = LineLabelTasker(
            path2lines=self.path2lines,
            path2docs=self.path2docs,
            manifest_path=self.manifest_path,
            config_path=self.config_path,
            tmp_dir="/tmp/tasker_test",
            config=self.config
        )
        return tasker

    def _test_task_archive(self, task_path: str) -> None:
        self.assertTrue(os.path.isfile(task_path))
        with ZipFile(task_path) as archive:
            namelist = [name.split("/", maxsplit=1)[-1] for name in archive.namelist()]
            self.assertIn("test_config.json", namelist)
            self.assertIn("test_manifest.md", namelist)
            images_paths = [image for image in archive.namelist() if "_img_bbox_" in image]
            self.assertTrue(len(images_paths) > 0)
            for image_path in images_paths:
                with archive.open(image_path) as image_file:
                    image = Image.open(image_file)
                    self.assertEqual((1276, 1754), image.size)
