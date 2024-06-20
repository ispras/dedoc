import json
import os
import shutil
import tempfile
import zipfile
from collections import OrderedDict
from typing import Tuple

import wget

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.attachments_extractors.concrete_attachments_extractors.pdf_attachments_extractor import PDFAttachmentsExtractor
from dedoc.config import get_config
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader


def get_reader_attachments(reader: BaseReader, input_dir: str, attachments_dir: str) -> dict:
    os.makedirs(attachments_dir)
    result_dict = OrderedDict()

    for file_name in sorted(os.listdir(input_dir)):
        if not file_name.endswith("pdf") or file_name == "large.pdf":
            continue

        attachment_names = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, file_name)
            shutil.copy(os.path.join(input_dir, file_name), file_path)
            document = reader.read(file_path, parameters={"with_attachments": "true"})
            os.remove(file_path)

            file_attachments_dir = os.path.join(attachments_dir, file_name.replace(".", "_"))
            os.makedirs(file_attachments_dir)

            png_files, json_files = 0, 0
            for attachment in document.attachments:
                if os.path.isfile(attachment.tmp_file_path):
                    attachment_name, png_files, json_files = _get_attachment_name(attachment, png_files, json_files)
                    shutil.copy(attachment.tmp_file_path, os.path.join(file_attachments_dir, attachment_name))
                    attachment_names.append(attachment_name)

        print(f"{file_name}: {len(attachment_names)} attachments, {len(document.attachments)} in result")
        result_dict[file_name] = sorted(attachment_names)

    return result_dict


def get_attachments(attachments_extractor: AbstractAttachmentsExtractor, input_dir: str, attachments_dir: str) -> dict:
    os.makedirs(attachments_dir)
    result_dict = OrderedDict()

    for file_name in sorted(os.listdir(input_dir)):
        if not file_name.endswith("pdf"):
            continue

        attachment_names = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, file_name)
            shutil.copy(os.path.join(input_dir, file_name), file_path)
            attachments = attachments_extractor.extract(file_path=file_path)
            os.remove(file_path)

            file_attachments_dir = os.path.join(attachments_dir, file_name.replace(".", "_"))
            os.makedirs(file_attachments_dir)

            png_files, json_files = 0, 0
            for attachment in attachments:
                if os.path.isfile(attachment.tmp_file_path):
                    attachment_name, png_files, json_files = _get_attachment_name(attachment, png_files, json_files)
                    shutil.copy(attachment.tmp_file_path, os.path.join(file_attachments_dir, attachment_name))
                    attachment_names.append(attachment_name)

        print(f"{file_name}: {len(attachment_names)} attachments, {len(attachments)} in result")
        result_dict[file_name] = sorted(attachment_names)

    return result_dict


def _get_attachment_name(attachment: AttachedFile, png_files: int, json_files: int) -> Tuple[str, int, int]:
    attachment_name = attachment.original_name
    if attachment_name.endswith(".png"):
        png_files += 1
        attachment_name = f"{png_files}.png"
    if attachment_name.endswith(".json"):
        json_files += 1
        attachment_name = f"{json_files}.json"
    return attachment_name, png_files, json_files


if __name__ == "__main__":
    data_url = "https://at.ispras.ru/owncloud/index.php/s/EoczXGwWzai8ztN/download"
    data_dir = os.path.join(get_config()["intermediate_data_path"], "benchmark_pdf_attachments")

    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
        archive_path = os.path.join(data_dir, "with_attachments.zip")
        wget.download(data_url, archive_path)
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(data_dir)
        os.remove(archive_path)

        print(f"Benchmark data downloaded to {data_dir}")
    else:
        print(f"Use cached benchmark data from {data_dir}")

    in_dir = os.path.join(data_dir, "with_attachments")
    out_dir = os.path.join(in_dir, "extracted_attachments")

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    benchmarks_dict = {}

    print("Get tabby attachments")
    tabby_reader = PdfTabbyReader(config={})
    tabby_out_dir = os.path.join(out_dir, "tabby")
    benchmarks_dict["tabby"] = get_reader_attachments(reader=tabby_reader, input_dir=in_dir, attachments_dir=tabby_out_dir)

    print("Get pdfminer attachments")
    pdfminer_reader = PdfTxtlayerReader(config={})
    pdfminer_out_dir = os.path.join(out_dir, "pdfminer")
    benchmarks_dict["pdfminer"] = get_reader_attachments(reader=pdfminer_reader, input_dir=in_dir, attachments_dir=pdfminer_out_dir)

    print("Get common attachments")
    common_out_dir = os.path.join(out_dir, "common")
    pdf_attachments_extractor = PDFAttachmentsExtractor(config={})
    benchmarks_dict["common"] = get_attachments(attachments_extractor=pdf_attachments_extractor, input_dir=in_dir, attachments_dir=common_out_dir)

    json_out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "benchmarks"))
    with open(os.path.join(json_out_dir, "benchmark_pdf_attachments.json"), "w") as f:
        json.dump(benchmarks_dict, f, ensure_ascii=False, indent=2)

    print(f"Attachments were extracted to {out_dir}")
