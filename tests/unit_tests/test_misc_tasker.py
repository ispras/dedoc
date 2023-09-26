import json
import os
import tempfile
import unittest
import zipfile
from zipfile import ZipFile

from PIL import Image

from dedoc.attachments_handler.attachments_handler import AttachmentsHandler
from dedoc.converters.file_converter import FileConverterComposition
from dedoc.dedoc_manager import DedocManager
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from dedoc.metadata_extractors.metadata_extractor_composition import MetadataExtractorComposition
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_constructors.concrete_structure_constructors.tree_constructor import TreeConstructor
from dedoc.structure_constructors.structure_constructor_composition import StructureConstructorComposition
from dedoc.structure_extractors.concrete_structure_extractors.classifying_law_structure_extractor import ClassifyingLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.foiv_law_structure_extractor import FoivLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.law_structure_excractor import LawStructureExtractor
from dedoc.structure_extractors.structure_extractor_composition import StructureExtractorComposition
from dedoc.train_dataset.taskers.concrete_taskers.line_label_tasker import LineLabelTasker
from dedoc.train_dataset.taskers.images_creators.concrete_creators.docx_images_creator import DocxImagesCreator
from dedoc.train_dataset.taskers.images_creators.concrete_creators.txt_images_creator import TxtImagesCreator
from dedoc.train_dataset.taskers.tasker import Tasker
from dedoc.train_dataset.train_dataset_utils import get_path_original_documents
from tests.test_utils import get_test_config


class TestTasker(unittest.TestCase):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "taskers"))
    path2bboxes = os.path.join(base_path, "bboxes.jsonlines")
    path2lines = os.path.join(base_path, "lines.jsonlines")
    path2docs = os.path.join(base_path, "images")
    manifest_path = os.path.join(base_path, "test_manifest.md")
    config_path = os.path.join(base_path, "test_config.json")

    def test_paths(self) -> None:
        self.assertTrue(os.path.isfile(self.path2bboxes), self.path2bboxes)
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
                    path2bboxes=self.path2bboxes,
                    path2lines=self.path2lines,
                    path2docs=self.path2docs,
                    manifest_path=self.manifest_path,
                    config_path=self.config_path,
                    tmp_dir=tmpdir,
                    config=get_test_config()
                )
            }
            tasker = Tasker(boxes_label_path=self.path2bboxes,
                            line_info_path=self.path2lines,
                            images_path=self.path2docs,
                            save_path=tmpdir,
                            concrete_taskers=taskers,
                            config=get_test_config())
            tasks_path, task_size = tasker.create_tasks(type_of_task="law_classifier", task_size=1)
            self.assertTrue(os.path.isfile(tasks_path))
            self.assertEqual(1, task_size)
            with ZipFile(tasks_path) as archive:
                self.assertIn("original_documents.zip", archive.namelist())

    def _get_line_label_classifier(self) -> LineLabelTasker:
        config = get_test_config()
        tasker = LineLabelTasker(
            path2bboxes=self.path2bboxes,
            path2lines=self.path2lines,
            path2docs=self.path2docs,
            manifest_path=self.manifest_path,
            config_path=self.config_path,
            tmp_dir="/tmp/tasker_test",
            config=config
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

    def test_images_creators(self) -> None:
        test_dict = {"english_doc.docx": 3, "txt_example.txt": 7}
        config = get_test_config()
        config["labeling_mode"] = True
        path2docs = get_path_original_documents(config)
        files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "images_creator"))
        images_creators = [DocxImagesCreator(path2docs, config=get_test_config()), TxtImagesCreator(path2docs, config=get_test_config())]

        test_manager = DedocManager(manager_config=self.__create_test_manager_config(config), config=config)
        for doc in os.listdir(files_dir):
            if not doc.endswith(("docx", "txt")):
                continue

            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(os.path.join(tmp_dir, "archive.zip"), "w") as archive:
                    _ = test_manager.parse(file_path=os.path.join(files_dir, doc), parameters=dict(document_type="law"))
                    lines_path = os.path.join(config["intermediate_data_path"], "lines.jsonlines")
                    self.assertTrue(os.path.isfile(lines_path))
                    with open(lines_path, "r") as f:
                        lines = [json.loads(line) for line in f]
                    original_doc = lines[0]["original_document"]
                    path = os.path.join(get_path_original_documents(config), original_doc)
                    self.assertTrue(os.path.isfile(path))
                    for images_creator in images_creators:
                        if images_creator.can_read(lines):
                            images_creator.add_images(page=lines, archive=archive)
                            break
                    self.assertEqual(len(archive.namelist()), test_dict[doc])
            os.remove(path)
            os.remove(lines_path)

        config.pop("labeling_mode")

    def __create_test_manager_config(self, config: dict) -> dict:
        readers = [DocxReader(config=config), RawTextReader(config=config)]
        metadata_extractors = [BaseMetadataExtractor()]
        law_extractors = {
            FoivLawStructureExtractor.document_type: FoivLawStructureExtractor(config=config),
            LawStructureExtractor.document_type: LawStructureExtractor(config=config)
        }
        structure_extractors = {
            DefaultStructureExtractor.document_type: DefaultStructureExtractor(),
            ClassifyingLawStructureExtractor.document_type: ClassifyingLawStructureExtractor(extractors=law_extractors, config=config)
        }

        return dict(
            converter=FileConverterComposition(converters=[]),
            reader=ReaderComposition(readers=readers),
            structure_extractor=StructureExtractorComposition(extractors=structure_extractors, default_key="other"),
            structure_constructor=StructureConstructorComposition(default_constructor=TreeConstructor(), constructors={"tree": TreeConstructor()}),
            document_metadata_extractor=MetadataExtractorComposition(extractors=metadata_extractors),
            attachments_handler=AttachmentsHandler(config=config)
        )
