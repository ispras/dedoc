import argparse
from pathlib import Path

PAGES_NUMBERS = [1, 5, 10, 25, 50, 100]

docs = {
    "rosatom_docs": [
        "DAE (India) Annual Report 2020-21.pdf",
        "DAE (India) Annual Report 2021-22.pdf",
        "DAE (India) Annual Report 2022-23.pdf",
        "DAE (India) Annual Report 2023-24.pdf",
        "NNSA Annual Report 2020.pdf",
        "NNSA Annual Report 2021.pdf",
        "NNSA Annual Report 2022.pdf",
        "NNSA Annual Report 2023.pdf",
        "NNSA Annual Report 2024.pdf",
        "World Nuclear Industry Status Report 2024.pdf",
        "World Nuclear Industry Status Report 2025.pdf",
    ],
    "fintoc/sp": [
        "7-AENA_Informe_Anual_2015.pdf",
        "12-Endesa_Informe_de_Actividades_2016.pdf",
        "12-Endesa_Informe_de_Actividades_2017.pdf",
        "14-Ferrovial_Informe_Anual_2014.pdf",
        "15-Bankia_Informe_ Anual_2015.pdf",
        "15-Bankia_Informe_Anual_2015.pdf",
        "15-Bankia_Informe_Anual_2017.pdf",
        "20-Mapfre_Informe_Integrado_2017.pdf",
        "26-CatalanaOccidente_Informe_Anual_2016.pdf",
        "33-CIEAutomotive_Informe_Anual_2015.pdf",
        "33-CIEAutomotive_Informe_Anual_2016.pdf",
        "38-Alba_Informe_Anual_2015.pdf",
        "40-Logista_Informe_Anual_2017.pdf",
        "82-Pharma_Mar_Informe_Anual_2016.pdf",
        "115-Abengoa_Informe_Anual_2016.pdf",
        "114-Abengoa_Informe Anual_2017.pdf",
        "60-CAF_Informe_Anual_2014.pdf",
        "60-CAF_Informe_Anual_2015.pdf",
        "72-Realia_Informe_Anual_2017.pdf",
    ]
}

import os
import random

from pypdf import PdfReader, PdfWriter


def extract_random_pages(input_pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)

    for n in PAGES_NUMBERS:
        n_dir = output_dir / str(n)
        os.makedirs(n_dir, exist_ok=True)
        random_pages = sorted(random.sample(range(total_pages), n))
        writer = PdfWriter()
        for page_num in random_pages:
            writer.add_page(reader.pages[page_num])
        output_path = n_dir / input_pdf_path.name

        with output_path.open('wb') as out_f:
            writer.write(out_f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('in_dir', type=Path)
    parser.add_argument('out_dir', type=Path)
    args = parser.parse_args()

    for dir_name, files in docs.items():
        for file_name in files:
            file_path = args.in_dir / dir_name / file_name
            extract_random_pages(file_path, args.out_dir)
