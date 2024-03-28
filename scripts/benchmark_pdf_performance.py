import argparse
import json
import os.path
from typing import List

from scripts.benchmark_utils.pdf_performance_task import PDFPerformanceTask


def get_tasks(configs: List[dict], input_path: str, dedoc_host: str, pdf_options: List[str]) -> List[List[PDFPerformanceTask]]:
    tasks = []

    for config in configs:
        config_tasks = []

        for task_name in sorted(os.listdir(input_path)):
            files_path = os.path.join(input_path, task_name)
            if os.path.isdir(files_path) and not task_name.startswith("_"):
                config_tasks.append(PDFPerformanceTask(dedoc_host, task_name, files_path, pdf_options, config))

        tasks.append(config_tasks)

    return tasks


def make_report(tasks: List[List[PDFPerformanceTask]], output_path: str, configs: List[dict]) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("""<html>
        <head>
            <title>PDF performance benchmark</title>
            <style>
                p { margin-bottom: 5px; }
                pre { background: #f0f0f0; padding: 5px; margin: 0; }
                summary { font-weight: bold; font-size: 1.2em; margin-bottom: 5px; margin-top: 20px; }
                table { border-collapse: collapse; }
                td, th { padding: 5px 10px; border: 1px solid #000; text-align: center; }
                td:first-child { text-align: left; max-width: 600px; word-break: break-word; }
                td:last-child, tr:last-child td:not(:first-child) { background: #f0f0f0; }
                tr:last-child td:first-child { font-weight: bold; text-align: right; cursor: pointer; }
                .hidden-files tr:nth-child(n+3) { display: none; }
                .hidden-files tr:last-child { display: table-row; }
            </style>

            <script>
                function HideFiles(cell) {
                    cell.parentNode.parentNode.classList.toggle("hidden-files")
                }
            </script>
        </head>
        <body>""")

        for config, config_tasks in zip(configs, tasks):
            f.write("<p>Running parameters:</p>")
            f.write(f"<pre>{json.dumps(config, ensure_ascii=False, indent=2)}</pre>\n\n")

            for task in config_tasks:
                f.write(task.to_html())

        f.write("</body>\n")
        f.write("</html>\n")


def main() -> None:
    pdf_options = ["true", "false", "auto", "auto_tabby", "tabby"]
    parser = argparse.ArgumentParser(description="Script for evaluate different PDF readers performance.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--input", help="path to the directory with pdfs (default: %(default)s)", type=str, default="pdf_data")
    parser.add_argument("-o", "--output", help="path to the report filename (default: %(default)s)", type=str, default="pdf_performance.html")
    parser.add_argument("-n", "--loops", help="number of repetitions of testing one file (default: %(default)d)", type=int, default=1)
    parser.add_argument("--dedoc-host", help="url to DEDOC instance for sending files (default: %(default)s", type=str, default="http://localhost:1231")
    parser.add_argument("--pdf-options", help="values of pdf_with_text_layer argument", choices=pdf_options, nargs="+", required=True)
    parser.add_argument("--parameters", help="path to json file with alternative parameters dictionaries")
    args = parser.parse_args()

    assert os.path.exists(args.input), f'Directory "{args.input}" does not exists'
    assert os.path.isdir(args.input), f'Path "{args.input}" is not a directory'
    assert args.loops > 0, "The number of repetitions of testing one file must be positive"

    print(f'Run pdf performance benchmark with next pdf options: {", ".join(args.pdf_options)}')
    configs = [{}]

    if args.parameters:
        with open(args.parameters, "r", encoding="utf-8") as f:
            configs = json.load(f)

    tasks = get_tasks(configs, args.input, args.dedoc_host, args.pdf_options)

    for _ in range(args.loops):
        for config_tasks in tasks:
            for task in config_tasks:
                task.run()
                make_report(tasks, args.output, configs)


if __name__ == "__main__":
    main()
