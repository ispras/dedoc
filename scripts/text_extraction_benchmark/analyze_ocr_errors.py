import os
import re
from typing import List, Tuple

from texttable import Texttable

def __parse_ocr_errors(lines: List[str]) -> List:
    ocr_errors = []
    matched_errors = [(line_num, line) for line_num, line in enumerate(lines) if "Errors   Marked   Correct-Generated" in line][0]
    for line in lines[matched_errors[0] + 1:]:
        # example line: " 2        0   { 6}-{б}"
        errors = re.findall(r"(\d+)", line)[0]
        chars = re.findall(r"{(.*)}-{(.*)}", line)[0]
        ocr_errors.append([errors, chars[0], chars[1]])

    return ocr_errors

def __parse_symbol_info(lines: List[str]) -> Tuple[List, int]:
    symbols_info = []
    matched_symbols = [(line_num, line) for line_num, line in enumerate(lines) if "Count   Missed   %Right" in line][-1]
    start_block_line = matched_symbols[0]

    for line in lines[start_block_line + 1:]:
        # example line: "1187       11    99.07   {<\n>}"
        row_values = [value.strip() for value in re.findall(r"\d+.\d*|{\S+|\W+}", line)]
        row_values[-1] = row_values[-1][1:-1]  # get symbol value
        symbols_info.append(row_values)
    # Sort errors
    symbols_info = sorted(symbols_info, key=lambda row: int(row[1]), reverse=True)  # by missed

    return symbols_info, start_block_line


def get_summary_symbol_error(path_reports: str) -> Texttable:
    # 1 - call accsum for get summary of all reports
    accuracy_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "accsum"))

    if os.path.exists(f"{path_reports}/../accsum_report.txt"):
        os.remove(f"{path_reports}/../accsum_report.txt")

    file_reports = " ".join([os.path.join(path_reports, f) for f in os.listdir(path_reports) if os.path.isfile(os.path.join(path_reports, f))])

    command = f"{accuracy_script_path} {file_reports} >> {path_reports}/../accsum_report.txt"
    os.system(command)
    accsum_report_path = os.path.join(path_reports, "..", "accsum_report.txt")

    # 2 - parse report info
    with open(accsum_report_path, "r") as f:
        lines = f.readlines()

        symbols_info, start_symbol_block_line = __parse_symbol_info(lines)
        ocr_errors = __parse_ocr_errors(lines[:start_symbol_block_line - 1])

    # 3 - calculate ocr errors according to a symbol
    ocr_errors_by_symbol = {}
    for symbol_info in symbols_info:
        ocr_errors_by_symbol[symbol_info[-1]] = []
        for ocr_err in ocr_errors:
            if ocr_err[-1] == "" or len(ocr_err[-2]) > 3 or len(ocr_err[-1]) > 3:  # to ignore errors with long text (len > 3) or without text
                continue
            if symbol_info[-1] in ocr_err[-2]:
                ocr_errors_by_symbol[symbol_info[-1]].append(f"{ocr_err[0]} & <{ocr_err[1]}> -> <{ocr_err[2]}>")

    # 4 - create table with OCR errors
    ocr_err_by_symbol_table = Texttable()
    title = [["Symbol", "Cnt Errors & Correct-Generated"]]
    ocr_err_by_symbol_table.add_rows(title)
    for symbol, value in ocr_errors_by_symbol.items():
        if len(value) != 0:
            ocr_err_by_symbol_table.add_row([symbol, value])

    return ocr_err_by_symbol_table