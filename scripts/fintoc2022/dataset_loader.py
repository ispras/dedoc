import gzip
import json
import logging
import os
import pickle
import shutil
import tempfile
import zipfile
from collections import Counter, defaultdict
from typing import Dict, List

import wget
from Levenshtein._levenshtein import ratio

from dedoc.config import get_config
from dedoc.readers import PdfTabbyReader, PdfTxtlayerReader
from train_dataset.data_structures.line_with_label import LineWithLabel


class FintocLineWithLabelExtractor:
    """
    Create LineWithLabel from documents and their annotations
    """

    def __init__(self) -> None:
        self.readers = {"tabby": PdfTabbyReader(), "txt_layer": PdfTxtlayerReader()}

    def get_lines(self, file_name: str, file_path: str, gt_path: str, reader_name: str) -> List[LineWithLabel]:
        """
        Extract lines from PDF document, create labels for lines from the groundtruth file given by FinTOC.
        Labeled lines are matched to the lines extracted by dedoc using Levenshtein distance (threshold=0.8).

        :param file_name: name of the file (PDF, json)
        :param file_path: path to the PDF document
        :param gt_path: path to the groundtruth JSON file with labels
        :param reader_name: ("tabby", "txt_layer") - type of PDF reader used for lines extraction
        :return: document in form of list of lines with labels
        """
        document = self.readers[reader_name].read(file_path, parameters={"need_header_footer_analysis": "True"})

        labeled_lines = defaultdict(list)
        with open(gt_path) as gt_file:
            for labeled_line in json.load(gt_file):
                labeled_lines[labeled_line["page"] - 1].append(labeled_line)

        result = []
        for line in document.lines:
            page_candidates = [(ratio(line.line, labeled_line["text"]), labeled_line) for labeled_line in labeled_lines[line.metadata.page_id]]
            best_line = max(page_candidates, key=lambda t: t[0], default=(0, {}))
            depth = best_line[1]["depth"] if len(page_candidates) > 0 and best_line[0] > 0.8 else "-1"
            result.append(LineWithLabel(line=line.line, metadata=line.metadata, annotations=line.annotations, label=str(depth), group=file_name, uid=line.uid))

        return sorted(result, key=lambda x: (x.metadata.page_id, x.metadata.line_id))


class FintocDatasetLoader:
    """
    Class for downloading data from the cloud, distributing lines into document groups and sorting them.
    Returns data in form of document lines with their labels.
    """
    def __init__(self, dataset_dir: str, logger: logging.Logger) -> None:
        """
        :param dataset_dir: path to the directory where to store downloaded dataset
        :param logger: logger for logging details of dataset loading
        """
        self.dataset_dir = dataset_dir
        self.logger = logger
        self.config = get_config()
        self.data_url = "https://at.ispras.ru/owncloud/index.php/s/EZfm71WimN2h7rC/download"
        self.line_extractor = FintocLineWithLabelExtractor()

    def get_data(self, language: str, reader_name: str, use_cache: bool = True) -> Dict[str, List[LineWithLabel]]:
        """
        Download data from a cloud at `self.data_url` and sort document lines.

        :param language: ("en", "fr", "sp") - language group
        :param reader_name: ("tabby", "txt_layer") - type of reader for lines extraction from PDF
        :param use_cache: whether to use cached data (if dataset is already downloaded) or download it anyway
        :return: dict of documents {document path: document}, where document is a list of lines with labels of the training dataset
        """
        archive_path = os.path.join(self.dataset_dir, "dataset.zip")
        if not os.path.isfile(archive_path):
            os.makedirs(self.dataset_dir, exist_ok=True)
            self.logger.info("Start download dataset")
            wget.download(self.data_url, archive_path)
            self.logger.info(f"Finish download dataset to {archive_path}")

        pkl_path = os.path.join(self.dataset_dir, f"lines_{language}_{reader_name}.pkl.gz")

        if os.path.isfile(pkl_path) and use_cache:
            with gzip.open(pkl_path) as input_file:
                parsed_files = pickle.load(input_file)
            self.logger.info(f"Data were loaded from the local disk: {len(parsed_files)} files")
            return parsed_files

        result = self.__read_pdf_lines(archive_path, language, reader_name)

        with gzip.open(pkl_path, "wb") as out:
            pickle.dump(obj=result, file=out)
        self.logger.info(Counter([line.label for document in result.values() for line in document]))
        return result

    def __read_pdf_lines(self, archive_path: str, language: str, reader_name: str) -> Dict[str, List[LineWithLabel]]:
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(self.dataset_dir)

        data_dir = os.path.join(self.dataset_dir, "data", language)
        pdf_dir = os.path.join(data_dir, "pdf")
        gt_dir = os.path.join(data_dir, "annots")
        pdf_files = {pdf_file[:-len(".pdf")]: os.path.join(pdf_dir, pdf_file) for pdf_file in os.listdir(pdf_dir) if pdf_file.endswith(".pdf")}
        gt_files = {gt_file[:-len(".pdf.fintoc4.json")]: os.path.join(gt_dir, gt_file) for gt_file in os.listdir(gt_dir) if gt_file.endswith(".json")}
        assert set(pdf_files) == set(gt_files)

        result = {}
        with tempfile.TemporaryDirectory() as tmp_dir:
            for file_name in pdf_files:
                pdf_tmp_path = os.path.join(tmp_dir, file_name) + ".pdf"
                shutil.copy(pdf_files[file_name], pdf_tmp_path)
                try:
                    document = self.line_extractor.get_lines(file_name=file_name, file_path=pdf_tmp_path, gt_path=gt_files[file_name], reader_name=reader_name)
                    result[pdf_files[file_name]] = document
                except Exception as e:
                    self.logger.warning(f"Failed to read {file_name} by {reader_name}, error: {e}")
        return result
