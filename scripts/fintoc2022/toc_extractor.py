import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from typing import List

import wget
from PyPDF2 import PdfFileReader, PdfFileWriter
from dedoc.data_structures.line_with_meta import LineWithMeta
from tqdm import tqdm

from config import _config as config
from doc_reader.line_type_classifier.feature_extractor.toc_feature_extractor import TOCFeatureExtractor
from doc_reader.readers.scanned_reader.pdftxtlayer_reader.pdf_with_text_reader import PdfWithTextReader

toc_item = re.compile(r'"([^"]+)" (\d+)')
reader = PdfWithTextReader(config=config)


def get_one_columns_lines(path: str) -> List[LineWithMeta]:
    if path.startswith("file://"):
        path = path[len("file://"):]
    with tempfile.TemporaryDirectory() as tmpdir:
        path_tmp = os.path.join(tmpdir, os.path.basename(path))
        pdf_reader = PdfFileReader(path)
        writer = PdfFileWriter()
        for page_id in range(0, min(9, pdf_reader.getNumPages())):
            writer.addPage(pdf_reader.getPage(page_id))
        with open(path_tmp, 'wb') as write_file:
            writer.write(write_file)
        return reader.read(path=path_tmp, document_type=None, parameters={"is_one_column_document": True,
                                                                          "need_header_footer_analysis": "True"}).lines


def get_automatic_toc(path: str) -> List[dict]:
    result = []
    cmd = "pdftocio -p {}".format(path)
    with os.popen(cmd) as out:
        toc = out.readlines()
        if toc:
            for line in toc:
                match = toc_item.match(line.strip())
                if match:
                    result.append({"text": match.group(1), "page": match.group(2)})
        return result


def main(dir_out: str):
    toc_extractor = TOCFeatureExtractor()
    os.makedirs(dir_out, exist_ok=True)
    data_url = "https://at.ispras.ru/owncloud/index.php/s/EZfm71WimN2h7rC/download"
    print("use 'pip install -U pdf.tocgen' to install tool for automatic toc extraction")
    subprocess.run("pip install -U pdf.tocgen".split(" "))

    root = "/tmp/.fintoc/"
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    archive = os.path.join(root, "dataset.zip")
    wget.download(data_url, archive)
    with zipfile.ZipFile(archive, 'r') as zip_ref:
        zip_ref.extractall(root)
    data_dir = os.path.join(root, "data")

    for lang in ("en", "fr", "sp"):
        pdf_dir = os.path.join(data_dir, lang, "pdf")
        lang_dir_out = os.path.join(dir_out, lang)
        if os.path.isdir(lang_dir_out):
            shutil.rmtree(lang_dir_out)
        os.makedirs(lang_dir_out)

        tocs = {}
        for file in tqdm(os.listdir(pdf_dir)):
            if not file.endswith(".pdf"):
                continue
            path = os.path.join(pdf_dir, file)
            toc = get_automatic_toc(path)
            if len(toc) == 0:
                lines = get_one_columns_lines(path)
                toc = toc_extractor.get_toc(lines)
            doc_name = file[: -len(".pdf")]
            tocs[doc_name] = toc
            with open(os.path.join(lang_dir_out, f"{doc_name}_toc.json"), "w") as out:
                json.dump(obj=toc, fp=out, indent=4, ensure_ascii=False)

        with open(os.path.join(dir_out, f"{lang}_toc.json"), "w") as out:
            json.dump(tocs, out)


main(dir_out="/home/nasty/fintoc2022/toc")
