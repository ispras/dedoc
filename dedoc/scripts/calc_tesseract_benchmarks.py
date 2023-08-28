import os
import re
import zipfile
from tempfile import TemporaryDirectory
from typing import Dict, List

import cv2
import numpy as np
import pytesseract
import wget
from texttable import Texttable

from dedoc.config import get_config


def _call_tesseract(image: np.ndarray, language: str, psm: int = 3) -> str:
    config = f"--psm {psm}"
    text = pytesseract.image_to_string(image, lang=language, output_type=pytesseract.Output.DICT, config=config)["text"]
    return text


def _init_statistics_by_dataset(statistics: Dict, dataset_name: str) -> Dict:
    statistics[dataset_name] = {
        "Accuracy": [],
        "ASCII_Spacing_Characters": [],
        "ASCII_Special_Symbols": [],
        "ASCII_Digits": [],
        "ASCII_Uppercase_Letters": [],
        "Latin1_Special_Symbols": [],
        "Cyrillic": [],
        "Amount of words": []
    }

    return statistics


def _update_statistics_by_symbol_kind(statistics_dataset: List, pattern: str, lines: List) -> List:
    matched = [line for line in lines if pattern in line]
    if matched:
        statistics_dataset.append(float(re.findall(r"\d+\.\d+", matched[0])[0][:-1]))

    return statistics_dataset


def _update_statistics_by_dataset(statistics: Dict, dataset: str, accuracy_path: str, word_cnt: int) -> Dict:
    statistic = statistics[dataset]
    with open(accuracy_path, "r") as f:
        lines = f.readlines()
        matched = [line for line in lines if "Accuracy After Correction" in line]
        if not matched:
            matched = [line for line in lines if "Accuracy\n" in line]
        acc_percent = re.findall(r"\d+\.\d+", matched[0])[0][:-1]
        statistic["Accuracy"].append(float(acc_percent))
        statistic["Amount of words"].append(word_cnt)

        statistic["ASCII_Spacing_Characters"] = _update_statistics_by_symbol_kind(statistic["ASCII_Spacing_Characters"], "ASCII Spacing Characters", lines)
        statistic["ASCII_Special_Symbols"] = _update_statistics_by_symbol_kind(statistic["ASCII_Special_Symbols"], "ASCII Special Symbols", lines)
        statistic["ASCII_Digits"] = _update_statistics_by_symbol_kind(statistic["ASCII_Digits"], "ASCII Digits", lines)
        statistic["ASCII_Spacing_Characters"] = _update_statistics_by_symbol_kind(statistic["ASCII_Spacing_Characters"], "ASCII Spacing Characters", lines)
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
            sum(statistics[dataset]["Amount of words"]),
            _get_avg(statistics[dataset]["Accuracy"])]


if __name__ == "__main__":
    base_zip = "data_tesseract_benchmarks"
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "benchmarks"))
    cache_dir = os.path.join(get_config()["intermediate_data_path"], "tesseract_data")
    os.makedirs(cache_dir, exist_ok=True)
    benchmark_data_path = os.path.join(cache_dir, f"{base_zip}.zip")

    if not os.path.isfile(benchmark_data_path):
        wget.download("https://at.ispras.ru/owncloud/index.php/s/HqKt53BWmR8nCVG/download", benchmark_data_path)
        print(f"Benchmark data downloaded to {benchmark_data_path}")
    else:
        print(f"Use cached benchmark data from {benchmark_data_path}")
    assert os.path.isfile(benchmark_data_path)

    accs = [["Dataset", "Image name", "--psm", "Amount of words", "Accuracy OCR"]]
    accs_common = [["Dataset", "ASCII_Spacing_Chars", "ASCII_Special_Symbols", "ASCII_Digits",
                    "ASCII_Uppercase_Chars", "Latin1_Special_Symbols", "Cyrillic", "Amount of words", "AVG Accuracy"]]
    statistics = {}

    with zipfile.ZipFile(benchmark_data_path, "r") as arch_file:
        names_dirs = [member.filename for member in arch_file.infolist() if member.file_size > 0]
        abs_paths_to_files = [name.split("/")[:] for name in names_dirs]

        datasets = set([paths[1] for paths in abs_paths_to_files])

        for dataset_name in sorted(datasets):
            statistics = _init_statistics_by_dataset(statistics, dataset_name)
            imgs = [paths[3] for paths in abs_paths_to_files if paths[1] == dataset_name and paths[2] == "imgs"]

            for img_name in sorted(imgs):
                base_name, ext = os.path.splitext(img_name)
                if ext not in [".txt", ".png", ".tiff", ".tif", ".jpg"]:
                    continue

                gt_path = os.path.join(base_zip, dataset_name, "gts", f"{base_name}.txt")
                imgs_path = os.path.join(base_zip, dataset_name, "imgs", img_name)
                accuracy_path = os.path.join(cache_dir, f"{dataset_name}_{base_name}_accuracy.txt")

                with TemporaryDirectory() as tmpdir:
                    tmp_gt_path = os.path.join(tmpdir, "tmp_gt.txt")
                    tmp_ocr_path = os.path.join(tmpdir, "tmp_ocr.txt")

                    try:
                        with arch_file.open(gt_path) as gt_file, open(tmp_gt_path, "wb") as tmp_gt_file, open(tmp_ocr_path, "w") as tmp_ocr_file:

                            gt_text = gt_file.read().decode("utf-8")
                            word_cnt = len(gt_text.split())

                            tmp_gt_file.write(gt_text.encode())  # extraction gt from zip
                            tmp_gt_file.flush()

                            arch_file.extract(imgs_path, tmpdir)
                            image = cv2.imread(tmpdir + "/" + imgs_path)

                            # call ocr
                            psm = 6 if dataset_name == "english-words" else 4
                            text = _call_tesseract(image, "rus+eng", psm=psm)
                            tmp_ocr_file.write(text)
                            tmp_ocr_file.flush()

                            # calculation accuracy build for Ubuntu from source https://github.com/eddieantonio/ocreval
                            accuracy_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "accuracy"))
                            command = f"{accuracy_script_path} {tmp_gt_path} {tmp_ocr_path} >> {accuracy_path}"
                            os.system(command)

                            statistics = _update_statistics_by_dataset(statistics, dataset_name, accuracy_path, word_cnt)
                            accs.append([dataset_name, base_name, psm, word_cnt, statistics[dataset_name]["Accuracy"][-1]])

                    except Exception as ex:
                        print(ex)
                        print("If you have problems with libutf8proc.so.2, try the command: `apt install -y libutf8proc-dev`")

    table_aacuracy_per_image = Texttable()
    table_aacuracy_per_image.add_rows(accs)

    # calculating average accuracy for each data set
    table_common = Texttable()

    for dataset_name in sorted(statistics.keys()):
        row = [dataset_name]
        row.extend(_get_avg_by_dataset(statistics, dataset_name))
        accs_common.append(row)
    table_common.add_rows(accs_common)

    with open(os.path.join(output_dir, "tesseract_benchmark.txt"), "w") as res_file:
        res_file.write(f"Tesseract version is {pytesseract.get_tesseract_version()}\nTable 1 - Accuracy for each file\n")
        res_file.write(table_aacuracy_per_image.draw())
        res_file.write(f"\n\nTable 2 - AVG by each type of symbols:\n")
        res_file.write(table_common.draw())

    print(f"Tesseract version is {pytesseract.get_tesseract_version()}")
    print(table_aacuracy_per_image.draw())
    print(table_common.draw())
