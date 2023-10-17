import json
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import requests

from dedoc.api.api_utils import json2txt
from dedoc.dedoc_manager import DedocManager


URL = "https://at.ispras.ru/owncloud/index.php/s/uImxYhliBHU8ei7/download"

if __name__ == "__main__":
    response = requests.get(URL)
    info = dict()
    with TemporaryDirectory() as tmpdir:
        with (Path(tmpdir) / "pdfs.zip").open("wb") as f:
            f.write(response.content)
        import zipfile

        with zipfile.ZipFile((Path(tmpdir) / "pdfs.zip"), "r") as zip_ref:
            zip_ref.extractall((Path(tmpdir)))
        os.remove(Path(tmpdir) / "pdfs.zip")
        pdfs_path = Path(tmpdir) / "PdfMiner params "

        manager = DedocManager()
        for file in os.listdir(pdfs_path):
            result = manager.parse(file_path=str(pdfs_path / file), parameters={"pdf_with_text_layer": "true"})
            txt_content = json2txt(paragraph=result.content.structure)
            with (Path(tmpdir) / "ocr.txt").open("w") as f:
                f.write(txt_content)

            accuracy_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "accuracy"))
            gt_path = Path("pdf_ground_truths") / (file[:-3] + "txt")
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
        json.dump(info, f)

    print("save result in" + output_dir)
