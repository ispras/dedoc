import os
import time
from typing import List

from pdfminer.pdfpage import PDFPage

from dedoc.utils.utils import send_file
from scripts.benchmark_utils.performance_time import PerformanceResult


class PDFPerformanceTask:
    def __init__(self, dedoc_host: str, title: str, input_dir: str, pdf_reader_options: List[str], config: dict) -> None:
        self.dedoc_host = dedoc_host
        self.title = title
        self.config = config
        self.pdf_reader_options = pdf_reader_options

        filenames = [os.path.join(input_dir, filename) for filename in os.listdir(input_dir) if filename.endswith(".pdf")]
        self.times = {pdf_option: {filename: PerformanceResult() for filename in filenames} for pdf_option in self.pdf_reader_options}
        self.pages = {filename: self.__get_page_count(filename) for filename in filenames}
        self.filenames = sorted(filenames, key=lambda filename: self.pages[filename])

    def run(self) -> None:
        print(f'Run task "{self.title}"')

        for pdf_option in self.pdf_reader_options:
            print(f'  Handle files with pdf option "{pdf_option}":')
            self.__run_files(pdf_option)

    def to_html(self) -> str:
        if not self.filenames:
            return ""

        pdf_header = "".join(f"<th>{pdf_option}</th>" for pdf_option in self.pdf_reader_options)

        html = [
            "<details open>",
            f"<summary>{self.title} ({len(self.filenames)} files)</summary>", "<table>",
            f'<tr><th rowspan="2">Filename</th><th rowspan="2">Pages</th><th colspan="{len(self.pdf_reader_options) + 1}">pdf_with_text_layer</th></tr>',
            f"<tr>{pdf_header}<th>average</th></tr>"
        ]

        for filename in self.filenames:
            times = [self.times[pdf_option][filename] for pdf_option in self.pdf_reader_options]
            pages = self.pages[filename]
            html.append(f"<tr><td>{os.path.basename(filename)}</td><td>{pages}</td>{self.__get_performance_cells(times, pages)}</tr>")

        times = []
        for pdf_option in self.pdf_reader_options:
            times.append(PerformanceResult([self.times[pdf_option][filename] / self.pages[filename] for filename in self.filenames]))

        html.append(f'<tr><td colspan="2" onclick="HideFiles(this)">average (per page)</td>{self.__get_performance_cells(times)}</tr>')
        html.append("</table>")
        html.append("</details>\n")

        return "\n".join(html)

    def __run_file(self, pdf_option: str, filename: str) -> float:
        start_time = time.time()
        send_file(self.dedoc_host, os.path.basename(filename), filename, {"pdf_with_text_layer": pdf_option, **self.config})
        return time.time() - start_time

    def __run_files(self, pdf_option: str) -> None:
        for i, filename in enumerate(self.filenames):
            elapsed_time = self.__run_file(pdf_option, filename)
            self.times[pdf_option][filename].add(elapsed_time)
            print(f'  - handle file {i + 1} / {len(self.filenames)} "{os.path.basename(filename)}" (pages: {self.pages[filename]}): {elapsed_time} seconds')

        print("")

    def __get_performance_cells(self, pdf_times: List[PerformanceResult], pages: int = 0) -> str:
        total_times = pdf_times + [PerformanceResult(pdf_times)]
        return "".join(f"<td>{times} ({times / pages} / page)</td>" if pages > 0 else f"<td>{times}</td>" for times in total_times)

    def __get_page_count(self, path: str) -> int:
        with open(path, "rb") as fp:
            pages = len(list(PDFPage.get_pages(fp)))

        return max(pages, 1)
