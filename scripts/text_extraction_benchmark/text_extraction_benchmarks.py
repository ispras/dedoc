import os
import re
import time
import zipfile
from enum import Enum
from typing import Dict, List, Tuple

import numpy as np
import pytesseract
import wget
from texttable import Texttable

from dedoc.config import get_config
from dedoc.readers import PdfImageReader
from scripts.text_extraction_benchmark.analyze_ocr_errors import get_summary_symbol_error

correction = Enum("Correction", ["SAGE_CORRECTION", "WITHOUT_CORRECTION"])

USE_CORRECTION_OCR = correction.WITHOUT_CORRECTION

reader = PdfImageReader()


def _get_text_from_image(path: str, language: str) -> str:
    document = reader.read(file_path=path, parameters={"language": language})
    return document.get_text()


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
    return [
        _get_avg(statistics[dataset]["ASCII_Spacing_Characters"]),
        _get_avg(statistics[dataset]["ASCII_Special_Symbols"]),
        _get_avg(statistics[dataset]["ASCII_Digits"]),
        _get_avg(statistics[dataset]["ASCII_Uppercase_Letters"]),
        _get_avg(statistics[dataset]["Latin1_Special_Symbols"]),
        _get_avg(statistics[dataset]["Cyrillic"]),
        sum(statistics[dataset]["Amount of words"]),
        _get_avg(statistics[dataset]["Accuracy"])
    ]


def __create_statistic_tables(statistics: dict, accuracy_values: List) -> Tuple[Texttable, Texttable]:
    accs = [["Dataset", "Image name", "OCR language", "Amount of words", "Accuracy OCR"]]
    accs_common = [
        [
            "Dataset", "ASCII_Spacing_Chars", "ASCII_Special_Symbols", "ASCII_Digits", "ASCII_Uppercase_Chars", "Latin1_Special_Symbols", "Cyrillic",
            "Amount of words", "AVG Accuracy"
        ]
    ]

    table_accuracy_per_image = Texttable()
    accs.extend(accuracy_values)
    table_accuracy_per_image.add_rows(accs)

    # calculating average accuracy for each data set
    table_common = Texttable()

    for dataset_name in sorted(statistics.keys()):
        row = [dataset_name]
        row.extend(_get_avg_by_dataset(statistics, dataset_name))
        accs_common.append(row)
    table_common.add_rows(accs_common)

    return table_common, table_accuracy_per_image


def calculate_accuracy_script(tmp_gt_path: str, tmp_prediction_path: str, accuracy_path: str) -> None:
    # calculation accuracy build for Ubuntu from source https://github.com/eddieantonio/ocreval
    accuracy_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "accuracy"))
    command = f"{accuracy_script_path} {tmp_gt_path} {tmp_prediction_path} >> {accuracy_path}"
    os.system(command)


def __calculate_ocr_reports(cache_dir_accuracy: str, benchmark_data_path: str, cache_dir: str) -> Tuple[Texttable, Texttable]:
    statistics = {}
    accuracy_values = []
    correction_times = []

    result_dir = os.path.join(cache_dir, "result_ocr")
    os.makedirs(result_dir, exist_ok=True)

    if USE_CORRECTION_OCR == correction.SAGE_CORRECTION:
        from scripts.text_extraction_benchmark.text_correction.sage_corrector import SageCorrector
        corrector = SageCorrector(cache_dir=cache_dir, use_gpu=True)

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
                accuracy_path = os.path.join(cache_dir_accuracy, f"{dataset_name}_{base_name}_accuracy.txt")
                if os.path.exists(accuracy_path):
                    os.remove(accuracy_path)

                tmp_gt_path = os.path.join(result_dir, f"{img_name}_gt.txt")
                result_ocr_filepath = os.path.join(result_dir, f"{img_name}_ocr.txt")

                try:
                    with arch_file.open(gt_path) as gt_file, open(tmp_gt_path, "wb") as tmp_gt_file, open(result_ocr_filepath, "w") as result_ocr_file:

                        gt_text = gt_file.read().decode("utf-8")
                        word_cnt = len(gt_text.split())

                        tmp_gt_file.write(gt_text.encode())  # extraction gt from zip
                        tmp_gt_file.close()

                        arch_file.extract(imgs_path, result_dir)

                        # 1 - call reader
                        language = "rus+eng" if dataset_name == "english-words" else "rus"
                        text = _get_text_from_image(path=result_dir + "/" + imgs_path, language=language)
                        result_ocr_file.write(text)
                        result_ocr_file.close()

                        # 2 - call correction step
                        time_b = time.time()
                        if USE_CORRECTION_OCR == correction.SAGE_CORRECTION:
                            corrected_text = corrector.correction(text)

                            result_ocr_filepath = os.path.join(corrector.corrected_path, f"{img_name}_ocr.txt")
                            with open(result_ocr_filepath, "w") as tmp_corrected_file:
                                tmp_corrected_file.write(corrected_text)
                        correction_times.append(time.time() - time_b)

                        # 3 - calculate accuracy from GTs and result texts
                        calculate_accuracy_script(tmp_gt_path, result_ocr_filepath, accuracy_path)
                        statistics = _update_statistics_by_dataset(statistics, dataset_name, accuracy_path, word_cnt)
                        accuracy_values.append([dataset_name, base_name, language, word_cnt, statistics[dataset_name]["Accuracy"][-1]])

                except Exception as ex:
                    print(ex)
                    print("If you have problems with libutf8proc.so.2, try the command: `apt install -y libutf8proc-dev`")

    print(f"Time mean correction ocr = {np.array(correction_times).mean()}")
    table_common, table_accuracy_per_image = __create_statistic_tables(statistics, accuracy_values)
    return table_common, table_accuracy_per_image


if __name__ == "__main__":
    base_zip = "data_tesseract_benchmarks"

    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "benchmarks"))
    cache_dir = os.path.join(get_config()["intermediate_data_path"], "tesseract_data")
    os.makedirs(cache_dir, exist_ok=True)
    cache_dir_accuracy = os.path.join(cache_dir, "accuracy")
    os.makedirs(cache_dir_accuracy, exist_ok=True)

    benchmark_data_path = os.path.join(cache_dir, f"{base_zip}.zip")
    if not os.path.isfile(benchmark_data_path):
        wget.download("https://at.ispras.ru/owncloud/index.php/s/gByenPIMlo0K7Gf/download", benchmark_data_path)
        print(f"Benchmark data downloaded to {benchmark_data_path}")
    else:
        print(f"Use cached benchmark data from {benchmark_data_path}")
    assert os.path.isfile(benchmark_data_path)

    table_common, table_accuracy_per_image = __calculate_ocr_reports(cache_dir_accuracy, benchmark_data_path, cache_dir)

    table_errors = get_summary_symbol_error(path_reports=cache_dir_accuracy)

    with open(os.path.join(output_dir, f"tesseract_benchmark_{USE_CORRECTION_OCR}.txt"), "w") as res_file:
        res_file.write(f"Tesseract version is {pytesseract.get_tesseract_version()}\n")
        res_file.write(f"Correction step: {USE_CORRECTION_OCR}\n")
        res_file.write("\nTable 1 - Accuracy for each file\n")
        res_file.write(table_accuracy_per_image.draw())
        res_file.write("\n\nTable 2 - AVG by each type of symbols:\n")
        res_file.write(table_common.draw())
        res_file.write("\n\nTable 3 -OCR error by symbol:\n")
        res_file.write(table_errors.draw())

    print(f"Tesseract version is {pytesseract.get_tesseract_version()}")
    print(table_accuracy_per_image.draw())
    print(table_common.draw())
    print(table_errors.draw())
