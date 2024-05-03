"""
This is a python3 script that rewrites the score function used in Book Structure
Extraction Competition @ ICDAR2013
(https://www.cs.helsinki.fi/u/doucet/papers/ICDAR2013.pdf).
It uses a classic levenshtein distance implemented by
https://pypi.org/project/python-Levenshtein/ instead of a customized levenshtein
distance.
It is used to score participants in FinTOC2020 shared task.

------
INSTALL
------
pip install python-Levenshtein

------
USAGE
------
python metric.fintoc2.py--gt_folder <gt_folder> --submission_folder <submission_folder>

<gt_folder> and <submission_folder> are paths to folders containing JSON files:
[
    {
        "text": String, # text of the TOC item/entry
        "id": Int # identifer of the item/entry corresponding to its order in the TOC
        "depth": Int # hierarchical level of the item
        "page": Int # the (physical) page number where the item appears
    }

]
"""

import argparse
import csv
import json
import logging
import os
from abc import ABC, abstractmethod
from glob import glob
from operator import itemgetter

import Levenshtein
import numpy as np

JSON_EXTENSION = ".fintoc4.json"
VERBOSE = True
STRING_THRESHOLD = 0.85


class TOCJson:
    def __init__(self, json_file):
        self.parse(json_file)

    def parse(self, json_file):
        with open(json_file, "r", encoding="utf-8") as infile:
            content = json.load(infile)
        self.entries = []
        for dict_entry in content:
            self.entries.append(Title(dict_entry["text"], dict_entry["page"], dict_entry["id"], dict_entry["depth"]))


class Title:
    def __init__(self, text, page_nb, id_, depth):
        self.text = text
        self.page_nb = page_nb
        self.id_ = id_
        self.depth = depth
        self.matched = False

    def __repr__(self):
        return f"page={self.page_nb} title={repr(self.text)}"

    def compare_page_nb(self, entry):
        if isinstance(entry.page_nb, str):
            entry.page_nb = int(entry.page_nb)
        if self.page_nb == entry.page_nb:
            return 0
        if self.page_nb > entry.page_nb:
            return 1
        return -1

    def compare_depth(self, entry):
        if str(self.depth) == entry.depth:
            return 0
        if str(self.depth) > entry.depth:
            return 1
        return -1


class ICDARMetric(ABC):

    def __init__(self):
        self.correct = 0
        self.added = 0
        self.missed = 0
        self.mismatch = 0
        self.p_per_doc = {}
        self.r_per_doc = {}
        self.f_per_doc = {}
        self.title_acc_per_doc = {}

    def compute_prf(self):
        self.compute_p()
        self.compute_r()
        try:
            self.f_score = 2 * self.prec * self.reca / (self.prec + self.reca)
        except ZeroDivisionError:
            self.f_score = 0
        return self.prec, self.reca, self.f_score

    def compute_p(self):
        try:
            self.prec = self.correct / (self.correct + self.added + self.mismatch)
        except ZeroDivisionError:
            self.prec = 0

    def compute_r(self):
        try:
            self.reca = self.correct / (self.correct + self.missed + self.mismatch)
        except ZeroDivisionError:
            self.reca = 0

    @abstractmethod
    def initialize_stats(self):
        self.correct = 0
        self.added = 0
        self.missed = 0
        self.mismatch = 0
        self.prec = 0.0
        self.reca = 0.0
        self.f_score = 0.0
        self.title_acc = 0.0

    @abstractmethod
    def get_title_acc(self, *args):
        pass

    def format_float_percent(self, float_nb):
        return "%.1f" % (100 * float_nb)

    def format_res(self):
        out = ["%6s" % self.format_float_percent(self.prec)]
        out.append("%6s" % self.format_float_percent(self.reca))
        out.append("%6s" % self.format_float_percent(self.f_score))
        out.append("%6s" % self.format_float_percent(self.title_acc))
        return out

    def compute_avg_p(self):
        return np.mean(list(self.p_per_doc.values()))

    def compute_std_p(self):
        return np.std(list(self.p_per_doc.values()))

    def compute_avg_r(self):
        return np.mean(list(self.r_per_doc.values()))

    def compute_std_r(self):
        return np.std(list(self.r_per_doc.values()))

    def compute_avg_f(self):
        return np.mean(list(self.f_per_doc.values()))

    def compute_std_f(self):
        return np.std(list(self.f_per_doc.values()))

    def compute_avg_title_acc(self):
        return np.mean(list(self.title_acc_per_doc.values()))

    def compute_std_title_acc(self):
        return np.std(list(self.title_acc_per_doc.values()))


class InexMetric(ICDARMetric):

    def __init__(self):
        super().__init__()
        self.level_correct = 0
        self.level_acc = 0.0
        self.level_acc_per_doc = {}

    def initialize_stats(self):
        super().initialize_stats()
        self.level_correct = 0
        self.level_acc = 0.0

    def get_level_acc(self, nb_valid_links):
        try:
            self.level_acc = self.level_correct / nb_valid_links
        except ZeroDivisionError:
            self.level_acc = 0.0
        return self.level_acc

    def get_title_acc(self, nb_valid_links):
        try:
            self.title_acc = self.correct / nb_valid_links
        except ZeroDivisionError:
            self.title_acc = 0.0
        return self.title_acc

    def format_res(self):
        out = super().format_res()
        out.append("%6s" % self.format_float_percent(self.level_acc))
        return out

    def compute_avg_level_acc(self):
        return np.mean(list(self.level_acc_per_doc.values()))

    def compute_std_level_acc(self):
        return np.std(list(self.level_acc_per_doc.values()))


class XeroxMetric(ICDARMetric):

    def __init__(self):
        super().__init__()
        self.text_sim = 0

    def initialize_stats(self):
        super().initialize_stats()
        self.text_sim = 0

    def get_title_acc(self):
        try:
            self.title_acc = self.text_sim / float(self.correct)
        except ZeroDivisionError:
            self.title_acc = 0.0
        return self.title_acc


class Stats:

    def __init__(self):
        self.ok_per_doc = {}
        self.pbttl_per_doc = {}
        self.pblvl_per_doc = {}
        self.err_per_doc = {}
        self.miss_per_doc = {}

    def compute_sum_ok(self):
        return sum(list(self.ok_per_doc.values()))

    def compute_sum_pbttl(self):
        return sum(list(self.pbttl_per_doc.values()))

    def compute_sum_pblvl(self):
        return sum(list(self.pblvl_per_doc.values()))

    def compute_sum_err(self):
        return sum(list(self.err_per_doc.values()))

    def compute_sum_miss(self):
        return sum(list(self.miss_per_doc.values()))


class Writer:

    def __init__(self):
        self.toc_rows = self.format_icdar_heading()
        self.td_rows = self.format_td_heading()

    @classmethod
    def format_icdar_heading(self):
        out = [
            "Doc", "Xrx-P", "Xrx-R", "Xrx-F1", "Xrx-Title acc", "Inex08-P", "Inex08-R",
            "Inex08-F1", "Inex08-Title acc", "Inex08-Level acc", "Ok", "PbTtl",
            "PbLvl", "Err", "Miss", "book id"
        ]
        return [out]

    @classmethod
    def format_td_heading(self):
        out = ["Doc", "Prec", "Rec", "F1", "Book id"]
        return [out]

    def dump_all(self):
        self.dump_toc()
        self.dump_td()

    def dump_toc(self):
        with open("toc_report.csv", "w", encoding="utf-8") as outfile:
            writer = csv.writer(outfile, dialect=csv.excel, delimiter="\t")
            writer.writerows(self.toc_rows)

    def dump_td(self):
        with open("td_report.csv", "w", encoding="utf-8") as outfile:
            writer = csv.writer(outfile, dialect=csv.excel, delimiter="\t")
            writer.writerows(self.td_rows)


def score_title_detection(toc1, toc2, log):
    correct = 0
    for entry1 in toc1.entries:
        res = find_matching_entry(entry1.text, toc2)
        if res is not None:
            index, match_score = res
            matched_text = toc2.entries[index].text
            msg = "Gt title %s is matched to %s (score=%.4g)" % (repr(entry1.text), repr(matched_text), match_score)
            log.info(msg)
            entry1.matched = True
            toc2.entries[index].matched = True
            correct += 1
        else:
            log.info(f"Gt title {repr(entry1.text)} is not matched to any submission title")
    for entry in toc2.entries:
        if not entry.matched:
            log.info(f"{entry} in submission not matched")
    added = len([entry for entry in toc2.entries if not entry.matched])
    missed = len([entry for entry in toc1.entries if not entry.matched])
    log.info("nb of added titles: %i", added)
    log.info("nb of missed titles: %i", missed)
    log.info("nb of correct titles: %i", correct)
    # return score
    try:
        prec = correct / (correct + added)
    except ZeroDivisionError:
        prec = 0.0
    try:
        reca = correct / (correct + missed)
    except ZeroDivisionError:
        reca = 0.0
    try:
        f1_score = 2 * prec * reca / (prec + reca)
    except ZeroDivisionError:
        f1_score = 0.0
    return prec, reca, f1_score


def find_matching_entry(text, toc):
    if len(toc.entries) == 0:
        return None
    similarities = []
    for entry in toc.entries:
        if not entry.matched:
            similarities.append(Levenshtein.ratio(text, entry.text))
        else:
            similarities.append(0)
    index, match_score = max(enumerate(similarities), key=itemgetter(1))
    if match_score > STRING_THRESHOLD:
        return index, match_score
    return None


def update_icdar_stats(toc1, toc2, inex_metric, xerox_metric, log):
    i1, i2 = 0, 0
    if len(toc1.entries) > 0 and len(toc2.entries) > 0:
        entry1 = toc1.entries[i1]
        entry2 = toc2.entries[i2]
        while True:
            link_result = entry1.compare_page_nb(entry2)
            try:
                if link_result == 0:
                    xerox_metric.correct += 1
                    text_similarity = Levenshtein.ratio(entry1.text, entry2.text)
                    xerox_metric.text_sim += text_similarity
                    if text_similarity > STRING_THRESHOLD:
                        inex_metric.correct += 1
                    else:
                        if VERBOSE:
                            log.info(f"TITLE ERROR: {entry1} <--> {repr(entry2.text)}")
                        inex_metric.mismatch += 1
                    depth_result = entry1.compare_depth(entry2)
                    if depth_result == 0:
                        inex_metric.level_correct += 1
                    i1 += 1
                    i2 += 1
                    entry1 = toc1.entries[i1]
                    entry2 = toc2.entries[i2]
                elif link_result < 0:
                    inex_metric.missed += 1
                    xerox_metric.missed += 1
                    if VERBOSE:
                        log.info(f"MISS: {entry1}")
                        i1 += 1
                        entry1 = toc1.entries[i1]
                else:
                    inex_metric.added += 1
                    xerox_metric.added += 1
                    if VERBOSE:
                        log.info(f"ADDED: {entry2}")
                    i2 += 1
                    entry2 = toc2.entries[i2]
            except IndexError:
                break
    # take into account remaining entries in gt
    while i1 < len(toc1.entries):
        if VERBOSE:
            entry1 = toc1.entries[i1]
            log.info(f"MISS: {entry1}")
        i1 += 1
        inex_metric.missed += 1
        xerox_metric.missed += 1
    # take into account remaining entries in submission
    while i2 < len(toc2.entries):
        if VERBOSE:
            entry2 = toc2.entries[i2]
            log.info(f"ADDED: {entry2}")
        i2 += 1
        inex_metric.added += 1
        xerox_metric.added += 1


def score(folder1, folder2):
    def get_docnames(folder, ext):
        out = []
        for ele in ls(folder, ext):
            out.append(basename(ele, ext))
        return out

    docnames1 = get_docnames(folder1, JSON_EXTENSION)
    docnames2 = get_docnames(folder2, JSON_EXTENSION)
    docnames = list(set(docnames1) & set(docnames2))
    n_missing_docs = len([ele for ele in docnames1 if ele not in docnames2])
    n_added_docs = len([ele for ele in docnames2 if ele not in docnames1])
    writer = Writer()
    doc_id = 0
    # TOC generation metrics
    inex = InexMetric()
    xerox = XeroxMetric()
    count = Stats()
    # Title detection metrics
    td_prec = dict(zip(docnames, [None] * len(docnames)))
    td_reca = dict(zip(docnames, [None] * len(docnames)))
    td_f1 = dict(zip(docnames, [None] * len(docnames)))
    # loggers
    toc_logger = get_logger("toc", "toc.log")
    td_logger = get_logger("td", "td.log")
    for json1 in ls(folder1, JSON_EXTENSION):
        xerox.initialize_stats()
        inex.initialize_stats()
        toc1 = TOCJson(json1)
        docname = basename(json1, JSON_EXTENSION)
        if VERBOSE:
            toc_logger.info(f"\n\nCOMPARING {docname}")
            td_logger.info(f"\n\nCOMPARING {docname}")
        json2 = os.path.join(folder2, docname + JSON_EXTENSION)
        if not os.path.isfile(json2):
            toc_logger.info(f"{docname} missing from submission")
            td_logger.info(f"{docname} missing from submission")
        else:
            # Title detection
            toc2 = TOCJson(json2)
            td_prec[docname], td_reca[docname], td_f1[docname] = score_title_detection(toc1, toc2, td_logger)
            writer.td_rows.append([doc_id, td_prec[docname], td_reca[docname], td_f1[docname], docname])
            # TOC generation
            update_icdar_stats(toc1, toc2, inex, xerox, toc_logger)
            # compute stats
            count.ok_per_doc[docname] = xerox.correct
            count.pbttl_per_doc[docname] = xerox.correct - inex.correct
            count.pblvl_per_doc[docname] = xerox.correct - inex.level_correct
            count.err_per_doc[docname] = xerox.added
            count.miss_per_doc[docname] = xerox.missed
            # compute Xerox score
            xerox.compute_prf()
            xerox.p_per_doc[docname] = xerox.prec
            xerox.r_per_doc[docname] = xerox.reca
            xerox.f_per_doc[docname] = xerox.f_score
            xerox.title_acc_per_doc[docname] = xerox.get_title_acc()
            # compute Inex score
            inex.compute_prf()
            inex.p_per_doc[docname] = inex.prec
            inex.r_per_doc[docname] = inex.reca
            inex.f_per_doc[docname] = inex.f_score
            inex.title_acc_per_doc[docname] = inex.get_title_acc(xerox.correct)
            inex.level_acc_per_doc[docname] = inex.get_level_acc(xerox.correct)
            # result row
            writer.toc_rows.append(get_row_result(doc_id, docname, xerox, inex))
            doc_id += 1
    # get avg and std scores
    writer.toc_rows.append(get_avg_row(xerox, inex, count))
    writer.toc_rows.append(get_std_row(xerox, inex))
    writer.td_rows.append(get_avg_row(td_prec, td_reca, td_f1))
    writer.td_rows.append(get_std_row(td_prec, td_reca, td_f1))
    # get stats about missing and added docs
    writer.toc_rows.append(
        [f"Done: {len(docnames)} comparisons for {len(docnames1)} in groundtruth and {len(docnames2)} in submission"])
    if n_missing_docs:
        writer.toc_rows.append([f"{n_missing_docs} docs missing from submission"])
    if n_added_docs:
        writer.toc_rows.append([f"{n_added_docs} additional docs in submission (ignored)"])
    # dump
    writer.dump_all()


def get_row_result(doc_id, doc, xerox, inex):
    out = ["%4s " % doc_id]
    out.extend(xerox.format_res())
    out.extend(inex.format_res())
    out.append("%7s" % xerox.correct)
    out.append("%7s" % (xerox.correct - inex.correct))
    out.append("%7s" % (xerox.correct - inex.level_correct))
    out.append("%7s" % xerox.added)
    out.append("%7s" % xerox.missed)
    out.append("%s" % doc)
    return out


"""
https://medium.com/practo-engineering/function-overloading-in-python-94a8b10d1e08
"""
registry = {}


class MultiMethod(object):
    def __init__(self, name):
        self.name = name
        self.typemap = {}

    def __call__(self, *args):
        types = tuple(arg.__class__ for arg in args)
        function = self.typemap.get(types)
        if function is None:
            raise TypeError("no match")
        return function(*args)

    def register(self, types, function):
        self.typemap[types] = function


def overload(*types):
    def register(function):
        name = function.__name__
        mm = registry.get(name)
        if mm is None:
            mm = registry[name] = MultiMethod(name)
        mm.register(types, function)
        return mm

    return register


"""
https://medium.com/practo-engineering/function-overloading-in-python-94a8b10d1e08
"""


@overload(XeroxMetric, InexMetric, Stats)
def get_avg_row(xerox, inex, count):
    out = []
    out.append("%4s " % "AVG")
    # xerox
    out.append("%6s" % xerox.format_float_percent(xerox.compute_avg_p()))
    out.append("%6s" % xerox.format_float_percent(xerox.compute_avg_r()))
    out.append("%6s" % xerox.format_float_percent(xerox.compute_avg_f()))
    out.append("%6s" % xerox.format_float_percent(xerox.compute_avg_title_acc()))
    # inex
    out.append("%6s" % inex.format_float_percent(inex.compute_avg_p()))
    out.append("%6s" % inex.format_float_percent(inex.compute_avg_r()))
    out.append("%6s" % inex.format_float_percent(inex.compute_avg_f()))
    out.append("%6s" % inex.format_float_percent(inex.compute_avg_title_acc()))
    out.append("%6s" % inex.format_float_percent(inex.compute_avg_level_acc()))
    # count stats
    out.append("%7s" % (count.compute_sum_ok()))
    out.append("%7s" % (count.compute_sum_pbttl()))
    out.append("%7s" % (count.compute_sum_pblvl()))
    out.append("%7s" % (count.compute_sum_err()))
    out.append("%7s" % (count.compute_sum_miss()))
    return out


@overload(XeroxMetric, InexMetric)
def get_std_row(xerox, inex):
    out = ["%4s " % "sdev"]
    # xerox
    out.append("%6s" % xerox.format_float_percent(xerox.compute_std_p()))
    out.append("%6s" % xerox.format_float_percent(xerox.compute_std_r()))
    out.append("%6s" % xerox.format_float_percent(xerox.compute_std_f()))
    out.append("%6s" % xerox.format_float_percent(xerox.compute_std_title_acc()))
    # inex
    out.append("%6s" % inex.format_float_percent(inex.compute_std_p()))
    out.append("%6s" % inex.format_float_percent(inex.compute_std_r()))
    out.append("%6s" % inex.format_float_percent(inex.compute_std_f()))
    out.append("%6s" % inex.format_float_percent(inex.compute_std_title_acc()))
    out.append("%6s" % inex.format_float_percent(inex.compute_std_level_acc()))
    return out


@overload(dict, dict, dict)
def get_avg_row(td_prec, td_reca, td_f1):
    return [
        "AVG",
        np.mean(list(td_prec.values())),
        np.mean(list(td_reca.values())),
        np.mean(list(td_f1.values()))
    ]


@overload(dict, dict, dict)
def get_std_row(td_prec, td_reca, td_f1):
    return [
        "stdev",
        np.std(list(td_prec.values())),
        np.std(list(td_reca.values())),
        np.std(list(td_f1.values()))
    ]


def get_logger(name, path_to_log, level=logging.ERROR):
    handler = logging.FileHandler(path_to_log, mode="w")
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


def basename(path, ext):
    return os.path.basename(path).split(ext)[0]


def ls(folder, ext):
    pattern = os.path.join(folder, "*" + ext)
    return glob(pattern)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="This is the scoring script used for FincTOC2021. It outputs two csv "
                                     "reports, one for title detection, and  another for toc generation. It also logs "
                                     "information in two separate log files.")
    PARSER.add_argument("--gt_folder", required=True, type=str, 
                        help="path to folder containing groundtruth files (one groundtruth file in json format per document")
    PARSER.add_argument("--submission_folder", required=True, type=str,
                        help="path to folder containing submission files (one submission file in json format per document")
    ARGS = PARSER.parse_args()
    score(ARGS.gt_folder, ARGS.submission_folder)
