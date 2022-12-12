import os
import argparse
import zipfile
from typing import List, Dict
from texttable import Texttable
import re
import pytesseract
import cv2
import numpy as np
from tempfile import TemporaryDirectory
import shutil


parser = argparse.ArgumentParser()
parser.add_argument("--input_path", "-i", type=str, default="../../resources/benchmarks/data_tesseract_benchmarks.zip")
parser.add_argument("--output_path", "-o", type=str, default="../../resources/benchmarks/")
parser.add_argument("--log_path", "-l", type=str, default="/tmp/dedoc/benchamarks/tesseract/")


def _call_tesseract(image: np.ndarray, language: str, psm: int = 3) -> str:
    config = "--psm {}".format(psm)
    text = pytesseract.image_to_string(image, lang=language, output_type=pytesseract.Output.DICT, config=config)['text']
    return text


def _init_statistics_by_dataset(statistics: Dict, dataset_name: str) -> Dict:
    statistics[dataset_name] = {
        "Accuracy": [],
        "ASCII_Spacing_Characters": [],
        "ASCII_Special_Symbols": [],
        "ASCII_Digits": [],
        "ASCII_Uppercase_Letters": [],
        "Latin1_Special_Symbols": [],
        "Cyrillic": []
    }

    return statistics


def _update_statistics_by_symbol_kind(statistics_dataset: List, pattern: str, lines: List) -> List:
    matched = [line for line in lines if pattern in line]
    if matched:
        statistics_dataset.append(float(re.findall(r"\d+\.\d+", matched[0])[0][:-1]))

    return statistics_dataset


def _update_statistics_by_dataset(statistics: Dict, dataset: str, accuracy_path: str) -> Dict:
    statistic = statistics[dataset]
    with open(accuracy_path, "r") as f:
        lines = f.readlines()
        matched = [line for line in lines if "Accuracy After Correction" in line]
        if not matched:
            matched = [line for line in lines if "Accuracy\n" in line]
        acc_percent = re.findall(r'\d+\.\d+', matched[0])[0][:-1]
        statistic["Accuracy"].append(float(acc_percent))

        statistic["ASCII_Spacing_Characters"] = _update_statistics_by_symbol_kind(statistic["ASCII_Spacing_Characters"],
                                                                                  "ASCII Spacing Characters",
                                                                                  lines)
        statistic["ASCII_Special_Symbols"] = _update_statistics_by_symbol_kind(statistic["ASCII_Special_Symbols"],
                                                                               "ASCII Special Symbols",
                                                                               lines)
        statistic["ASCII_Digits"] = _update_statistics_by_symbol_kind(statistic["ASCII_Digits"], "ASCII Digits", lines)
        statistic["ASCII_Spacing_Characters"] = _update_statistics_by_symbol_kind(statistic["ASCII_Spacing_Characters"],
                                                                                  "ASCII Spacing Characters",
                                                                                  lines)
        statistic["Cyrillic"] = _update_statistics_by_symbol_kind(statistic["Cyrillic"], "Cyrillic", lines)

    statistics[dataset] = statistic

    return statistics


def _get_avg(array: List) -> float:
    return sum(array) / len(array) if array else 0.0


def _get_avg_by_dataset(statistics: Dict, dataset: str) -> List:
    return [_get_avg(statistics[dataset]["ASCII_Spacing_Characters"]),
            _get_avg(statistics[dataset]["ASCII_Special_Symbols"]),
            _get_avg(statistics[dataset]["ASCII_Digits"]),
            _get_avg(statistics[dataset]["ASCII_Uppercase_Letters"]),
            _get_avg(statistics[dataset]["Latin1_Special_Symbols"]),
            _get_avg(statistics[dataset]["Cyrillic"]),
            _get_avg(statistics[dataset]["Accuracy"])]


if __name__ == "__main__":
    args = parser.parse_args()
    accs = [["Dataset", "Image name", "--psm", "Accuracy OCR"]]
    accs_common = [["Dataset", "ASCII_Spacing_Chars", "ASCII_Special_Symbols", "ASCII_Digits",
                    "ASCII_Uppercase_Chars", "Latin1_Special_Symbols", "Cyrillic", "AVG Accuracy"]]
    base_zip = "data_tesseract_benchmarks"

    statistics = {}

    if os.path.exists(args.log_path):
        shutil.rmtree(args.log_path)
    os.makedirs(args.log_path)

    with zipfile.ZipFile(args.input_path, 'r') as arch_file:
        names_dirs = [member.filename for member in arch_file.infolist() if member.file_size > 0]
        abs_paths_to_files = [name.split('/')[:] for name in names_dirs]

        datasets = set([paths[1] for paths in abs_paths_to_files])

        for dataset_name in sorted(datasets):
            statistics = _init_statistics_by_dataset(statistics, dataset_name)
            imgs = [paths[3] for paths in abs_paths_to_files if paths[1] == dataset_name and paths[2] == "imgs"]

            for img_name in sorted(imgs):
                base_name, ext = os.path.splitext(img_name)
                if ext not in ['.txt', '.png', '.tiff', '.tif', '.jpg']:
                    continue

                gt_path = os.path.join(base_zip, dataset_name, "gts", base_name + ".txt")
                imgs_path = os.path.join(base_zip, dataset_name, "imgs", img_name)
                accuracy_path = os.path.join(args.log_path, dataset_name + "_" + base_name + "_accuracy.txt")

                with TemporaryDirectory() as tmpdir:
                    tmp_gt_path = os.path.join(tmpdir, "tmp_gt.txt")
                    tmp_ocr_path = os.path.join(tmpdir, "tmp_ocr.txt")

                    try:
                        with arch_file.open(gt_path) as gt_file, \
                                open(tmp_gt_path, "wb") as tmp_gt_file,\
                                open(tmp_ocr_path, "w") as tmp_ocr_file:

                            tmp_gt_file.write(gt_file.read())  # extraction gt from zip
                            tmp_gt_file.flush()

                            arch_file.extract(imgs_path, tmpdir)
                            image = cv2.imread(tmpdir + "/" + imgs_path)

                            # call ocr
                            psm = 6 if dataset_name == "english-words" else 4
                            text = _call_tesseract(image, "rus+eng", psm=psm)
                            tmp_ocr_file.write(text)
                            tmp_ocr_file.flush()

                            # calculation accuracy build for Ubuntu from source https://github.com/eddieantonio/ocreval
                            command = "accuracy {} {} >> {}".format(tmp_gt_path, tmp_ocr_path, accuracy_path)
                            os.system(command)

                            statistics = _update_statistics_by_dataset(statistics, dataset_name, accuracy_path)
                            accs.append([dataset_name, base_name, psm, statistics[dataset_name]["Accuracy"][-1]])

                    except Exception as ex:
                        print(ex)

    table_aacuracy_per_image = Texttable()
    table_aacuracy_per_image.add_rows(accs)

    # calculating average accuracy for each data set
    table_common = Texttable()

    for dataset_name in sorted(statistics.keys()):
        row = [dataset_name]
        row.extend(_get_avg_by_dataset(statistics, dataset_name))
        accs_common.append(row)
    table_common.add_rows(accs_common)

    with open(os.path.join(args.output_path, "tesseract.benchmark"), "w") as res_file:
        res_file.write(
            "Tesseract version is {}\nTable 1 - Accuracy for each file\n".format(pytesseract.get_tesseract_version()))
        res_file.write(table_aacuracy_per_image.draw())
        res_file.write("\n\nTable 2 - AVG by each type of symbols:\n")
        res_file.write(table_common.draw())

    print("Tesseract version is {}".format(pytesseract.get_tesseract_version()))
    print(table_aacuracy_per_image.draw())
    print(table_common.draw())
