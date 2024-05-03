import os
import re
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from dedoc.config import get_config
from dedoc.data_structures import HierarchyLevel, LineWithMeta, UnstructuredDocument
from dedoc.structure_extractors import AbstractStructureExtractor
from dedoc.structure_extractors.feature_extractors.fintoc_feature_extractor import FintocFeatureExtractor
from dedoc.structure_extractors.feature_extractors.toc_feature_extractor import TOCFeatureExtractor
from dedoc.structure_extractors.line_type_classifiers.fintoc_classifier import FintocClassifier


class FintocStructureExtractor(AbstractStructureExtractor):
    """
    This class is an implementation of the TOC extractor for the `FinTOC 2022 Shared task <https://wp.lancs.ac.uk/cfie/fintoc2022/>`_.
    The code is a modification of the winner's solution (ISP RAS team).

    This structure extractor is used for English, French and Spanish financial prospects in PDF format (with a textual layer).
    It is recommended to use :class:`~dedoc.readers.PdfTxtlayerReader` to obtain document lines.
    You can find the more detailed description of this type of structure in the section :ref:`fintoc_structure`.
    """
    document_type = "fintoc"

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        from dedoc.readers import PdfTxtlayerReader  # to exclude circular imports
        self.pdf_reader = PdfTxtlayerReader(config=self.config)
        self.toc_extractor = TOCFeatureExtractor()
        self.features_extractor = FintocFeatureExtractor()
        self.languages = ("en", "fr", "sp")
        path = os.path.join(get_config()["resources_path"], "fintoc_classifiers")
        self.classifiers = {language: FintocClassifier(language=language, weights_dir_path=path) for language in self.languages}
        self.toc_item_regexp = re.compile(r'"([^"]+)" (\d+)')
        self.empty_string_regexp = re.compile(r"^\s*\n$")

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None, file_path: Optional[str] = None) -> UnstructuredDocument:
        """
        According to the `FinTOC 2022 <https://wp.lancs.ac.uk/cfie/fintoc2022/>`_ title detection task, lines are classified as titles and non-titles.
        The information about titles is saved in ``line.metadata.hierarchy_level`` (:class:`~dedoc.data_structures.HierarchyLevel` class):

            - Title lines have ``HierarchyLevel.header`` type, and their depth (``HierarchyLevel.level_2``) is similar to \
            the depth of TOC item from the FinTOC 2022 TOC generation task.
            - Non-title lines have ``HierarchyLevel.raw_text`` type, and their depth isn't obtained.

        :param document: document content that has been received from some of the readers (:class:`~dedoc.readers.PdfTxtlayerReader` is recommended).
        :param parameters: for this structure extractor, "language" parameter is used for setting document's language, e.g. ``parameters={"language": "en"}``. \
        The following options are supported:

            * "en", "eng" - English (default);
            * "fr", "fra" - French;
            * "sp", "spa" - Spanish.
        :param file_path: path to the file on disk.
        :return: document content with added additional information about title/non-title lines and hierarchy levels of titles.
        """
        parameters = {} if parameters is None else parameters
        language = self.__get_param_language(parameters=parameters)

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

    def __get_param_language(self, parameters: dict) -> str:
        language = parameters.get("language", "en")

        if language in ("en", "eng", "rus+eng"):
            return "en"

        if language in ("fr", "fra"):
            return "fr"

        if language in ("sp", "spa"):
            return "sp"

        if language not in self.languages:
            self.logger.warning(f"Language {language} is not supported by this extractor. Use default language (en)")
        return "en"

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

    def __get_toc(self, file_path: Optional[str]) -> List[Dict[str, Union[LineWithMeta, str]]]:
        """
        Try to get TOC from PDF automatically. If TOC wasn't extracted automatically, it is extracted using regular expressions.
        """
        if file_path is None or not file_path.lower().endswith(".pdf"):
            return []

        toc = self.__get_automatic_toc(path=file_path)
        if len(toc) > 0:
            self.logger.info(f"Got automatic TOC from {os.path.basename(file_path)}")
            return toc

        parameters = {"is_one_column_document": "True", "need_header_footer_analysis": "True", "pages": ":10"}
        lines = self.pdf_reader.read(file_path=file_path, parameters=parameters).lines
        return self.toc_extractor.get_toc(lines)

    def __get_automatic_toc(self, path: str) -> List[Dict[str, Union[LineWithMeta, str]]]:
        result = []
        with os.popen(f'pdftocio -p "{path}"') as out:
            toc = out.readlines()

        for line in toc:
            match = self.toc_item_regexp.match(line.strip())
            if match:
                result.append({"line": LineWithMeta(match.group(1)), "page": match.group(2)})

        return result
