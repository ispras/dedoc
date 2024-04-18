import gzip
import json
import os
import pickle
import re
import zipfile
from collections import defaultdict
from typing import Dict, Iterator, List, Optional, Tuple

import pandas as pd
import wget
from Levenshtein._levenshtein import ratio
from tqdm import tqdm

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_features_extractor import ListFeaturesExtractor
from dedoc.structure_extractors.feature_extractors.list_features.prefix.any_letter_prefix import AnyLetterPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_roman_prefix import BracketRomanPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bullet_prefix import BulletPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.empty_prefix import EmptyPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.letter_prefix import LetterPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.roman_prefix import RomanPrefix
from dedoc.structure_extractors.feature_extractors.paired_feature_extractor import PairedFeatureExtractor
from dedoc.structure_extractors.feature_extractors.toc_feature_extractor import TOCFeatureExtractor
from dedoc.structure_extractors.feature_extractors.utils_feature_extractor import normalization_by_min_max
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_year
from dedoc.utils.utils import flatten


class FintocFeatureExtractor(AbstractFeatureExtractor):

    def __init__(self, tocs: dict):
        self.paired_feature_extractor = PairedFeatureExtractor()
        self.prefix_list = [BulletPrefix, AnyLetterPrefix, LetterPrefix, BracketPrefix, BracketRomanPrefix, DottedPrefix, RomanPrefix]
        self.list_feature_extractors = [
            ListFeaturesExtractor(window_size=10, prefix_list=self.prefix_list),
            ListFeaturesExtractor(window_size=25, prefix_list=self.prefix_list),
            ListFeaturesExtractor(window_size=100, prefix_list=self.prefix_list)
        ]
        self.prefix2number = {prefix.name: i for i, prefix in enumerate(self.prefix_list, start=1)}
        self.prefix2number[EmptyPrefix.name] = 0
        self.tocs = tocs

    def parameters(self) -> dict:
        return {}

    def fit(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> "AbstractFeatureExtractor":
        return self

    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        assert len(documents) > 0
        result_matrix = pd.concat([self.__process_document(document) for document in tqdm(documents)], ignore_index=True)
        result_matrix = pd.concat([result_matrix, self.paired_feature_extractor.transform(documents)], axis=1)
        features = sorted(result_matrix.columns)
        result_matrix = result_matrix[features].astype(float)
        result_matrix["text"] = [line.line for line in flatten(documents)]
        features.append("text")
        return result_matrix[features]

    def __process_document(self, lines: List[LineWithMeta]) -> pd.DataFrame:
        features_df = pd.DataFrame(self.__look_at_prev_line(document=lines, n=1))
        features_df["line_relative_length"] = self.__get_line_relative_length(lines)

        list_features = pd.concat([f_e.one_document(lines)[1] for f_e in self.list_feature_extractors], axis=1)

        page_ids = [line.metadata.page_id for line in lines]
        start_page, finish_page = (min(page_ids), max(page_ids)) if page_ids else (0, 0)

        total_lines = len(lines)
        one_line_features_dict = defaultdict(list)
        for line_id, line in enumerate(lines):
            for item in self.__one_line_features(line, total_lines, start_page=start_page, finish_page=finish_page):
                feature_name, feature = item[0], item[1]
                one_line_features_dict[feature_name].append(feature)

        one_line_features_df = pd.DataFrame(one_line_features_dict)
        one_line_features_df["font_size"] = self._normalize_features(one_line_features_df.font_size)

        one_line_features_df = self.prev_next_line_features(one_line_features_df, 3, 3)
        result_matrix = pd.concat([one_line_features_df, features_df, list_features], axis=1)
        return result_matrix

    def __look_at_prev_line(self, document: List[LineWithMeta], n: int = 1) -> Dict[str, List]:
        """
        Look at previous line and compare with current line

        :param document: list of lines
        :param n: previous line number to look
        :return: dict of features
        """
        res = defaultdict(list)
        for line_id, line in enumerate(document):
            if line_id >= n:
                prev_line = document[line_id - n]
                is_prev_line_ends = prev_line.line.endswith(('.', ';'))
                res["prev_line_ends"].append(1 if is_prev_line_ends else 0)
                res["prev_ends_with_colon"].append(prev_line.line.endswith(":"))
                res["prev_is_space"].append(prev_line.line.lower().isspace())
            else:
                res["prev_line_ends"].append(0)
                res["prev_ends_with_colon"].append(0)
                res["prev_is_space"].append(0)
        return res

    def __get_line_relative_length(self, lines: List[LineWithMeta]) -> List[float]:
        max_len = max([len(line.line) for line in lines])
        relative_lengths = [len(line.line) / max_len for line in lines]
        return relative_lengths

    def __one_line_features(self, line: LineWithMeta, total_lines: int, start_page: int, finish_page: int) -> Iterator[Tuple[str, int]]:
        yield "normalized_page_id", normalization_by_min_max(line.metadata.page_id, min_v=start_page, max_v=finish_page)
        yield "indentation", self._get_indentation(line)
        yield "spacing", self._get_spacing(line)
        yield "bold", self._get_bold(line)
        yield "italic", self._get_italic(line)
        yield from self._get_color(line)
        yield "font_size", self._get_size(line)

        yield "line_id", normalization_by_min_max(line.metadata.line_id, min_v=0, max_v=total_lines)
        yield "num_year_regexp", len(regexps_year.findall(line.line))
        yield "endswith_dot", line.line.endswith(".")
        yield "endswith_semicolon", line.line.endswith(";")
        yield "endswith_colon", line.line.endswith(":")
        yield "endswith_comma", line.line.endswith(",")
        yield "startswith_bracket", line.line.strip().startswith(('(', '{'))

        bracket_cnt = 0
        for char in line.line:
            if char == '(':
                bracket_cnt += 1
            elif char == ')':
                bracket_cnt = max(0, bracket_cnt - 1)
        yield "bracket_num", bracket_cnt

        probable_toc_title = re.sub(r"[\s:]", "", line.line).lower()
        yield "is_toc_title", probable_toc_title in TOCFeatureExtractor.titles
        yield from self.__find_in_toc(line)

        line_length = len(line.line) + 1
        yield "supper_percent", sum((1 for letter in line.line if letter.isupper())) / line_length
        yield "letter_percent", sum((1 for letter in line.line if letter.isalpha())) / line_length
        yield "number_percent", sum((1 for letter in line.line if letter.isnumeric())) / line_length
        yield "words_number", len(line.line.split())

    def __find_in_toc(self, line: LineWithMeta) -> Iterator[Tuple[str, int]]:
        if not hasattr(line, "group"):
            yield "is_toc", 0
            yield "in_toc", 0
            yield "toc_exists", 0
        else:
            toc = self.tocs.get(line.group, [])
            is_toc = 0
            in_toc = 0
            toc_exists = int(len(toc) > 0)
            line_text = line.line.lower().strip()
            for item in toc:
                if ratio(line_text, item["text"].lower()) > 0.8:
                    is_toc = 0 if line.metadata.page_id + 1 == int(item["page"]) else 1
                    in_toc = 1 if line.metadata.page_id + 1 == int(item["page"]) else 0
                    break
            yield "is_toc", is_toc
            yield "in_toc", in_toc
            yield "toc_exists", toc_exists


def handle_file(file: str, dir_out: str, extractor: AbstractFeatureExtractor):
    file_name = os.path.split(file)[-1].split(".")[0]
    with gzip.open(file) as f_in:
        lines = pickle.load(file=f_in)
        df = lines2dataframe(lines, extractor)
        df.to_csv(os.path.join(dir_out, file_name + "_df.csv.gz"), index=False)
        df.to_pickle(os.path.join(dir_out, file_name + "_df.pkl.gz"))


def lines2dataframe(lines: List[LineWithLabel], extractor: AbstractFeatureExtractor) -> pd.DataFrame:
    assert(len(lines) > 0)
    lines2docs = []
    current_document = None
    reg_empty_string = re.compile(r"^\s*\n$")
    special_unicode_symbols = [u"\uf0b7", u"\uf0d8", u"\uf084", u"\uf0a7", u"\uf0f0", u"\x83"]

    lines = [line for line in lines if not reg_empty_string.match(line.line)]
    for line in lines:
        for ch in special_unicode_symbols:
            line.set_line(line.line.replace(ch, ""))
        if line.group == current_document:
            lines2docs[-1].append(line)
        else:
            current_document = line.group
            lines2docs.append([line])
    df = extractor.transform(lines2docs)

    df["label"] = [int(line.label) for line in lines]
    df["group"] = [line.group for line in lines]
    df["uid"] = [line.uid for line in lines]
    df["page_id"] = [line.metadata.page_id for line in lines]
    return df


def main(dir_out: str, train: bool):
    os.makedirs(dir_out, exist_ok=True)

    root = "/tmp/.fintoc/train" if train else "/tmp/.fintoc/test"
    lines_dir = os.path.join(root, "lines")
    if train:
        lines_url = "https://at.ispras.ru/owncloud/index.php/s/yvYn491d6Du8ZuV/download"  # train
    else:
        lines_url = "https://at.ispras.ru/owncloud/index.php/s/h3TdYfQipiVAxpE/download"  # test

    toc_dir = os.path.join(root, "toc")
    if train:
        toc_url = "https://at.ispras.ru/owncloud/index.php/s/0VJbQWrD11R98Sy/download"  # train
    else:
        toc_url = "https://at.ispras.ru/owncloud/index.php/s/GCoZitUsfCLPLVI/download"  # test

    if not os.path.isdir(root):
        os.makedirs(root)

    if not os.path.isdir(lines_dir):
        archive = os.path.join(root, "lines.zip")
        wget.download(lines_url, archive)
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            zip_ref.extractall(root)

    if not os.path.isdir(toc_dir):
        archive = os.path.join(root, "toc.zip")
        wget.download(toc_url, archive)
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            zip_ref.extractall(root)

    for lang in tqdm(["en", "fr", "sp"]):
        lines_file = os.path.join(lines_dir, f"lines_{lang}_txt_layer.pkg.gz")
        tocs_file = os.path.join(toc_dir, f"{lang}_toc.json")
        with open(tocs_file) as f:
            tocs = json.load(f)
        extractor = FintocFeatureExtractor(tocs)
        handle_file(file=lines_file, extractor=extractor, dir_out=dir_out)


if __name__ == '__main__':
    stage = "test"
    main(dir_out=f"/home/nasty/fintoc2022/{stage}/pandas", train=stage == "train")
