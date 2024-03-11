import json
import pprint
import zipfile
from pathlib import Path
from typing import List, Optional

import numpy as np
import wget

from dedoc.api.api_utils import table2html
from dedoc.config import get_config
from dedoc.readers import PdfImageReader
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer
from scripts.benchmark_table.metric import TEDS

path_result = Path(__file__).parent / ".." / ".." / "resources" / "benchmarks"
path_result.absolute().mkdir(parents=True, exist_ok=True)

table_recognizer = TableRecognizer(config=get_config())
image_reader = PdfImageReader(config=get_config())

GENERATED_BENCHMARK = "on_generated_data"
OURDATA_BENCHMARK = "on_our_data"
TYPE_BENCHMARK = OURDATA_BENCHMARK


def call_metric(pred_json: dict, true_json: dict, structure_only: bool = False, ignore_nodes: Optional[List] = None) -> dict:
    teds = TEDS(structure_only=structure_only, ignore_nodes=ignore_nodes)
    scores = teds.batch_evaluate(pred_json, true_json)
    pp = pprint.PrettyPrinter()
    pp.pprint(scores)

    return scores


def get_tables(image_path: Path, language: str) -> str:
    document = image_reader.read(str(image_path), {"language": language})

    for table in document.tables:
        table.metadata.uid = "test_id"
    table2id = {"test_id": 0}
    html_tables = [table2html(table, table2id) for table in document.tables]

    # TODO: while works with one table in an image
    return html_tables[0]


def make_predict_json(data_path: Path, language: str) -> dict:
    predict_json = {}
    for pathname in Path.iterdir(data_path):
        print(pathname)

        predict_json[pathname.name] = {"html": "<html><body>" + get_tables(pathname, language) + "</body></html>"}

    return predict_json


def download_dataset(data_dir: Path, name_zip: str, url: str) -> None:
    if Path.exists(data_dir):
        print(f"Use cached benchmark data from {data_dir}")
        return

    data_dir.mkdir(parents=True, exist_ok=True)
    pdfs_zip_path = data_dir / name_zip
    wget.download(url, str(data_dir))

    with zipfile.ZipFile(pdfs_zip_path, "r") as zip_ref:
        zip_ref.extractall(data_dir)
    pdfs_zip_path.unlink()

    print(f"Benchmark data downloaded to {data_dir}")


def prediction(path_pred: Path, path_images: Path, language: str = "rus+eng") -> dict:
    pred_json = make_predict_json(path_images, language)
    with path_pred.open("w") as fd:
        json.dump(pred_json, fd, indent=2, ensure_ascii=False)

    return pred_json


def benchmark_on_our_data() -> dict:
    data_dir = Path(get_config()["intermediate_data_path"]) / "benchmark_table_data"
    path_images = data_dir / "images"
    path_gt = data_dir / "gt.json"
    path_pred = data_dir / "pred.json"
    result = dict()
    download_dataset(data_dir, name_zip="benchmark_table_data.zip", url="https://at.ispras.ru/owncloud/index.php/s/nYgwbhVk5SpvD3z/download")

    mode_metric_structure_only = False

    with open(path_gt, "r") as fp:
        gt_json = json.load(fp)

    """
    # Creating base html (based on method predictions for future labeling)
    pred_json = prediction(data_dir / "gt_generated.json", path_images)
    """

    pred_json = prediction(path_pred, path_images)
    scores = call_metric(pred_json=pred_json, true_json=gt_json, structure_only=mode_metric_structure_only)

    result["mode_metric_structure_only"] = mode_metric_structure_only
    result["mean"] = np.mean([score for score in scores.values()])
    result["images"] = scores

    return result


def benchmark_on_generated_table() -> dict:
    """
    Generated data from https://github.com/hassan-mahmood/TIES_DataGeneration
    Article generation information https://arxiv.org/pdf/1905.13391.pdf
    Note: generate the 1st table tape category
    Note: don't use header table tag <th>, replacing on <td> tag
    Note: all generated data (four categories) you can download from
    TODO: some tables have a low quality. Should to trace the reason.
    All generated data (all categories) we can download from https://at.ispras.ru/owncloud/index.php/s/cjpCIR7I0G4JzZU
    """

    data_dir = Path(get_config()["intermediate_data_path"]) / "visualizeimgs" / "category1"
    path_images = data_dir / "img_500"
    path_gt = data_dir / "html_500"
    download_dataset(data_dir,
                     name_zip="benchmark_table_data_generated_500_tables_category_1.zip",
                     url="https://at.ispras.ru/owncloud/index.php/s/gItWxupnF2pve6B/download")
    mode_metric_structure_only = False

    # make common ground-truth file
    common_gt_json = {}
    for pathname in Path.iterdir(path_gt):
        image_name = pathname.name.split(".")[0] + ".png"
        with open(pathname, "r") as fp:
            table_html = fp.read()
            # exclude header tags
            table_html = table_html.replace("<th ", "<td ")
            table_html = table_html.replace("</th>", "</td>")

        common_gt_json[image_name] = {"html": table_html}

    file_common_gt = data_dir / "common_gt.json"
    with file_common_gt.open("w") as fd:
        json.dump(common_gt_json, fd, indent=2, ensure_ascii=False)

    # calculate metrics
    path_pred = data_dir / "pred.json"
    pred_json = prediction(path_pred, path_images, language="eng")
    scores = call_metric(pred_json=pred_json, true_json=common_gt_json, structure_only=mode_metric_structure_only,
                         ignore_nodes=["span", "style", "head", "h4", "tbody"])

    result = dict()
    result["mode_metric_structure_only"] = mode_metric_structure_only
    result["mean"] = np.mean([score for score in scores.values()])
    result["images"] = scores

    return result


if __name__ == "__main__":
    result = benchmark_on_our_data() if TYPE_BENCHMARK == OURDATA_BENCHMARK else benchmark_on_generated_table()

    # save benchmarks
    file_result = path_result / f"table_benchmark_{TYPE_BENCHMARK}.json"
    with file_result.open("w") as fd:
        json.dump(result, fd, indent=2, ensure_ascii=False)
