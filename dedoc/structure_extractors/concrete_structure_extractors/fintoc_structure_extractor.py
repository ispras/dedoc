import os
import re
import tempfile
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from PyPDF2 import PdfFileReader, PdfFileWriter

from dedoc.data_structures import HierarchyLevel, LineWithMeta, UnstructuredDocument
from dedoc.readers import PdfTxtlayerReader
from dedoc.structure_extractors import AbstractStructureExtractor
from dedoc.structure_extractors.feature_extractors.fintoc_feature_extractor import FintocFeatureExtractor
from dedoc.structure_extractors.feature_extractors.toc_feature_extractor import TOCFeatureExtractor
from dedoc.structure_extractors.line_type_classifiers.fintoc_classifier import FintocClassifier


class FintocStructureExtractor(AbstractStructureExtractor):
    """
    This class is an implementation of the TOC extractor for the `FinTOC 2022 Shared task<https://wp.lancs.ac.uk/cfie/fintoc2022/>`_.
    The code is a modification of the winner's solution (ISP RAS team).

    You can find the description of this type of structure in the section :ref:`fintoc_structure`.
    """
    document_type = "fintoc"

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.pdf_reader = PdfTxtlayerReader(config=self.config)
        self.toc_extractor = TOCFeatureExtractor()
        self.features_extractor = FintocFeatureExtractor()
        self.languages = ("en", "fr", "sp")
        self.classifiers = {language: FintocClassifier(language=language) for language in self.languages}
        self.toc_item_regexp = re.compile(r'"([^"]+)" (\d+)')
        self.empty_string_regexp = re.compile(r"^\s*\n$")

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None, file_path: Optional[str] = None) -> UnstructuredDocument:
        """

        To get the information about the method's parameters look at the documentation of the class \
        :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.
        """
        parameters = {} if parameters is None else parameters
        language = parameters.get("language", "en")
        if language not in self.languages:
            raise ValueError(f"Language {language} is not supported by this extractor. Supported languages: {self.languages}")

        features, documents = self.get_features(documents_dict={file_path: document.lines})
        predictions = self.classifiers[language].predict(features)
        lines: List[LineWithMeta] = documents[0]
        assert len(lines) == len(predictions)

        for line, prediction in zip(lines, predictions):
            if prediction > 0:
                line.metadata.hierarchy_level = HierarchyLevel(level_1=1, level_2=prediction, line_type=HierarchyLevel.header, can_be_multiline=True)
            else:
                line.metadata.hierarchy_level = HierarchyLevel.create_raw_text()
        document.lines = lines

        return document

    def get_features(self, documents_dict: Dict[str, List[LineWithMeta]]) -> Tuple[pd.DataFrame, List[List[LineWithMeta]]]:
        toc_lines, documents = [], []
        for file_path, document_lines in documents_dict.items():
            toc_lines.append(self.__get_toc(file_path=file_path))
            documents.append(self.__filter_lines(document_lines))
        features = self.features_extractor.transform(documents=documents, toc_lines=toc_lines)
        return features, documents

    def __filter_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        special_unicode_symbols = [u"\uf0b7", u"\uf0d8", u"\uf084", u"\uf0a7", u"\uf0f0", u"\x83"]

        lines = [line for line in lines if not self.empty_string_regexp.match(line.line)]
        for line in lines:
            for ch in special_unicode_symbols:
                line.set_line(line.line.replace(ch, ""))

        return lines

    def __get_toc(self, file_path: Optional[str]) -> Optional[List[Dict[str, Union[LineWithMeta, str]]]]:
        if file_path is None:
            return

        toc = self.__get_automatic_toc(path=file_path)
        if len(toc) > 0:
            return toc

        pdf_reader = PdfFileReader(file_path)
        writer = PdfFileWriter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = os.path.join(tmpdir, os.path.basename(file_path))
            for page_id in range(0, min(9, pdf_reader.getNumPages())):
                writer.addPage(pdf_reader.getPage(page_id))
            with open(tmp_path, "wb") as write_file:
                writer.write(write_file)
            lines = self.pdf_reader.read(file_path=tmp_path, parameters={"is_one_column_document": "True", "need_header_footer_analysis": "True"}).lines

        return self.toc_extractor.get_toc(lines)

    def __get_automatic_toc(self, path: str) -> List[Dict[str, Union[LineWithMeta, str]]]:
        result = []
        with os.popen(f"pdftocio -p {path}") as out:
            toc = out.readlines()
        if len(toc) == 0:
            return result

        for line in toc:
            match = self.toc_item_regexp.match(line.strip())
            if match:
                result.append({"line": LineWithMeta(match.group(1)), "page": match.group(2)})

        return result
