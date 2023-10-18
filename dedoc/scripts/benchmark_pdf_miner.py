import json
import os
import re
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import wget

from dedoc.api.api_utils import json2txt
from dedoc.config import get_config
from dedoc.dedoc_manager import DedocManager


URL = "https://at.ispras.ru/owncloud/index.php/s/uImxYhliBHU8ei7/download"
URL_GT = "https://at.ispras.ru/owncloud/index.php/s/SXsOTqxGaGO9wL9/download"

if __name__ == "__main__":
    data_dir = Path(get_config()["intermediate_data_path"]) /  "text_layer_correctness_data"
    benchmark_data_dir = data_dir / "benchmark_pdf_miner"

    if not os.path.isdir(benchmark_data_dir):
        benchmark_data_dir.mkdir(parents=True)
        wget.download(URL, str(benchmark_data_dir / "pdfs.zip"))
        wget.download(URL_GT, str(benchmark_data_dir / "pdfs_gt.zip"))

        with zipfile.ZipFile(benchmark_data_dir / "pdfs.zip", 'r') as zip_ref:
            zip_ref.extractall(benchmark_data_dir)
        os.remove(benchmark_data_dir / "pdfs.zip")
        with zipfile.ZipFile(benchmark_data_dir / "pdfs_gt.zip", 'r') as zip_ref:
            zip_ref.extractall(benchmark_data_dir)
        os.remove(benchmark_data_dir / "pdfs_gt.zip")

        print(f"Benchmark data downloaded to {benchmark_data_dir}")
    else:
        print(f"Use cached benchmark data from {benchmark_data_dir}")

    pdfs_path = benchmark_data_dir / "PdfMiner params "
    pdfs_gt_path = benchmark_data_dir / "PdfMiner Params GT"

    info = dict()
    with TemporaryDirectory() as tmpdir:
        manager = DedocManager()
        for file in os.listdir(pdfs_path):
            result = manager.parse(file_path=str(pdfs_path / file), parameters={"pdf_with_text_layer": "true"})
            txt_content = json2txt(paragraph=result.content.structure)
            with (Path(tmpdir) / "ocr.txt").open("w") as f:
                f.write(txt_content)

            accuracy_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "accuracy"))
            gt_path = pdfs_gt_path / (file[:-3] + "txt")
            tmp_ocr_path = Path(tmpdir) / "ocr.txt"
            accuracy_path = Path(tmpdir) / "accuracy.txt"
            if accuracy_path.exists():
                accuracy_path.unlink()
            command = f"{accuracy_script_path} \"{gt_path}\" {tmp_ocr_path} >> {accuracy_path}"
            os.system(command)

            with open(accuracy_path, "r") as f:
                lines = f.readlines()
                matched = [line for line in lines if "Accuracy After Correction" in line]
                if not matched:
                    matched = [line for line in lines if "Accuracy\n" in line]
                acc_percent = re.findall(r"\d+\.\d+", matched[0])[0][:-1]
                info[str(file)] = acc_percent

    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "benchmarks"))
    with (Path(output_dir) / "test_pdf_miner.json").open("w") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"save result in {output_dir}")
