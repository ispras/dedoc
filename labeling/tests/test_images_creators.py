import json
import os
import shutil
import tempfile
import unittest
import zipfile
from typing import Optional

from dedoc.attachments_handler.attachments_handler import AttachmentsHandler
from dedoc.config import get_config
from dedoc.converters.converter_composition import ConverterComposition
from dedoc.dedoc_manager import DedocManager
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from dedoc.metadata_extractors.metadata_extractor_composition import MetadataExtractorComposition
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_constructors.concrete_structure_constructors.tree_constructor import TreeConstructor
from dedoc.structure_constructors.structure_constructor_composition import StructureConstructorComposition
from dedoc.structure_extractors.concrete_structure_extractors.classifying_law_structure_extractor import ClassifyingLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.foiv_law_structure_extractor import FoivLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.law_structure_excractor import LawStructureExtractor
from dedoc.structure_extractors.structure_extractor_composition import StructureExtractorComposition
from dedoc.utils.train_dataset_utils import get_path_original_documents
from train_dataset.taskers.images_creators.concrete_creators.abstract_images_creator import AbstractImagesCreator
from train_dataset.taskers.images_creators.concrete_creators.docx_images_creator import DocxImagesCreator
from train_dataset.taskers.images_creators.concrete_creators.scanned_images_creator import ScannedImagesCreator
from train_dataset.taskers.images_creators.concrete_creators.txt_images_creator import TxtImagesCreator


class TestImagesCreators(unittest.TestCase):
    config = get_config()
    config["labeling_mode"] = True
    path2docs = get_path_original_documents(config)

    def setUp(self) -> None:
        self.path2docs = get_path_original_documents(self.config)

    def tearDown(self) -> None:
        lines_path = os.path.join(self.config["intermediate_data_path"], "lines.jsonlines")
        if os.path.exists(lines_path):
            os.remove(lines_path)

        if os.path.exists(self.path2docs):
            shutil.rmtree(self.path2docs)

    def test_docx_images_creator(self) -> None:
        docx_images_creator = DocxImagesCreator(self.path2docs, config=self.config)
        self.__test_images_creator(images_creator=docx_images_creator, doc_name="english_doc.docx", num_images=3)

    def test_txt_images_creator(self) -> None:
        txt_images_creator = TxtImagesCreator(self.path2docs, config=self.config)
        self.__test_images_creator(images_creator=txt_images_creator, doc_name="txt_example.txt", num_images=7)

    def test_scanned_images_creator(self) -> None:
        scanned_images_creator = ScannedImagesCreator(self.path2docs)
        self.__test_images_creator(
            images_creator=scanned_images_creator,
            doc_name="english_doc.pdf",
            num_images=3,
            parameters=dict(document_type="law", pdf_with_text_layer="true")
        )
        self.__test_images_creator(
            images_creator=scanned_images_creator,
            doc_name="english_doc.pdf",
            num_images=3,
            parameters=dict(document_type="law", pdf_with_text_layer="tabby")
        )
        self.__test_images_creator(images_creator=scanned_images_creator, doc_name="law_image.png", num_images=34)

    def __test_images_creator(self, images_creator: AbstractImagesCreator, doc_name: str, num_images: int, parameters: Optional[dict] = None) -> None:
        parameters = dict(document_type="law") if parameters is None else parameters
        files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "images_creators"))
        test_manager = DedocManager(manager_config=self.__create_test_manager_config(self.config), config=self.config)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(os.path.join(tmp_dir, "archive.zip"), "w") as archive:
                _ = test_manager.parse(file_path=os.path.join(files_dir, doc_name), parameters=parameters)
                lines_path = os.path.join(self.config["intermediate_data_path"], "lines.jsonlines")
                self.assertTrue(os.path.isfile(lines_path))
                with open(lines_path, "r") as f:
                    lines = [json.loads(line) for line in f]
                original_doc = lines[0]["original_document"]
                path = os.path.join(get_path_original_documents(self.config), original_doc)
                self.assertTrue(os.path.isfile(path), f"{path} does not exist")
                self.assertTrue(images_creator.can_read(lines))
                images_creator.add_images(page=lines, archive=archive)
                self.assertEqual(len(archive.namelist()), num_images)
        os.remove(lines_path)
        os.remove(path)

    def __create_test_manager_config(self, config: dict) -> dict:
        readers = [
            DocxReader(config=config),
            RawTextReader(config=config),
            PdfTxtlayerReader(config=config),
            PdfTabbyReader(config=config),
            PdfImageReader(config=config)
        ]
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
            converter=ConverterComposition(converters=[]),
            reader=ReaderComposition(readers=readers),
            structure_extractor=StructureExtractorComposition(extractors=structure_extractors, default_key="other"),
            structure_constructor=StructureConstructorComposition(default_constructor=TreeConstructor(), constructors={"tree": TreeConstructor()}),
            document_metadata_extractor=MetadataExtractorComposition(extractors=metadata_extractors),
            attachments_handler=AttachmentsHandler(config=config)
        )
