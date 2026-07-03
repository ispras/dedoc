import argparse
import math
import os
import random
from enum import Enum
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation


class RotateType(str, Enum):
    SKEW = "skew"
    ORIENT = "orient"


PAGES_NUMBERS = [5, 10, 25, 50, 100]
ROTATE_TYPES = [RotateType.SKEW]

docs = {
    "pdf_china": [
        "CIAE_Annual Report_2014en.pdf",
        "CIAE_Annual Report_2016en.pdf",
        "CIAE_Annual Report_2012en.pdf",
        "CIAE_Annual Report_2017en.pdf",
        "CIAE_Annual Report_2015en.pdf",
        "CIAE_Annual Report_2011en.pdf",
        "CIAE_Annual Report_2013en.pdf",
        "CIAE_Annual Report_2020en.pdf",
        "CIAE_Annual Report_2019en.pdf",
        "CIAE_Annual Report_2018en.pdf",
    ],
    "fintoc/en": [
        "LU0705072691-LU0705072345-LU0705072188_English_2015_RAM-LUX-Long-Sh-EmergingMarktesEq-.pdf",
        "HSBC_Global_Investment_Funds_2017_X_P_X_A.pdf",
        "LU0424369923-LU0424369766-LU0114314536-LU0063949068-LU0686792812-LU0061927850-LU0686794354_English_2013_ManConvertibles.pdf",
        "LU0800341645-LU0800341132-LU0800341991-LU0800341215-LU0800341058-LU0800341488-LU0800341306_English_2012_FranklinBrazilOpportunities.pdf",
        "FU_BF097_EN_2019-05-13_a5585d06-b4df-4b1e-bf30-3c1b5615cf74.pdf",
        "LU1057354992_English_2016_EchiquierEuropeanBondsAEUR.pdf",
        "LU0589944569-LU0348788117-LU1156968403-LU1254141333-LU0348791418_English_2011_AllianzEm-AsiaEq-.pdf",
        "LU0462973008-LU0512124362_English_2015_DNCAInvestMiura.pdf",
        "LU0309082104-LU0309082799-LU0309082369_English_2015_DNCAInvest-Infrastructures.pdf",
        "LU0949250459-LU0645132902-LU0229041164-LU0390138864-LU0188151251-LU0543370943-LU0195951883-LU0152904719-LU0188151095-LU0543370513-LU0889566138-LU0229948244-LU0229948087-LU0122613572-LU0229949648_English_2012_Franklin.pdf",
        "Prospectus-2016-02-01.pdf",
        "LU0641972152-LU0641972079_English_2015_DBPWMIGlobalAllocationTracker-.pdf",
        "LU0289452210_English_2015_DBPWMIIGISUSEquityPortfolioB.pdf",
        "LU0178440839-LU0178439401-LU0178439310-LU0178439666_English_2012_AllianzBestSty-Eu-Eq-.pdf",
        "LU0375979613-LU0375979290_English_2015_GISDyn-ControlPFCo.pdf",
        "LU0734574329-LU0734574162-LU0333227550-LU0333226230-LU0571576585-LU1039626509-LU0333227394-LU0333226826-LU0734574246-LU0333227048_English_2015_ML.pdf",
        "LU0881817786-LU0881818081-LU0881817430-LU0881817190_English_2014_OddoBondsHighYieldEurope.pdf",
        "LU0575375588-LU0493852429-LU0261074230-LU0640453774-LU0860716223-LU0575374698-LU0493865678-LU0860715415-LU0493851454-LU0160485420-LU0493867534-LU0860716140-LU0953070868-LU0956110364-LU0688432862_English_2016_AshmoreS.pdf",
        "LU1252823262-LU0482498846-LU0482498762-LU0955861710-LU0955867758-LU0955867915-LU0432616810-LU0607521506-LU0955867832-LU0482498176-LU0955861983-LU0955861801-LU0432616901_English_2013_InvescoBalanced-RiskAlloc-.pdf",
        "Lombard_Odier_Funds_2014_X_P_X_X.pdf",
    ]
}


def skew_page(page):
    angle = random.choice([1, -1]) * random.choice(range(1, 45))

    crop_box = page.cropbox
    box = page.mediabox
    w = float(crop_box.width)
    h = float(crop_box.height)
    margin_x = w * (0.05 + angle / 400)
    margin_y = h * (0.05 + angle / 400)
    page.mediabox.lower_left = (box.lower_left[0] - margin_x, box.lower_left[1] - margin_y)
    page.mediabox.upper_right = (box.upper_right[0] + margin_x, box.upper_right[1] + margin_y)
    page.cropbox = page.mediabox

    box = page.mediabox
    w = float(box.width)
    h = float(box.height)
    rad = math.radians(angle)
    cos_a = abs(math.cos(rad))
    sin_a = abs(math.sin(rad))

    center_x = w / 2
    center_y = h / 2

    transform = Transformation().translate(tx=-center_x, ty=-center_y)
    transform = transform.rotate(rotation=angle)
    transform = transform.translate(tx=center_x, ty=center_y)

    page.add_transformation(transform)

    new_width = w * cos_a + h * sin_a
    new_height = w * sin_a + h * cos_a

    x_offset = (new_width - w) / 2
    y_offset = (new_height - h) / 2

    page.mediabox.lower_left = (box.lower_left[0] - x_offset, box.lower_left[1] - y_offset)
    page.mediabox.upper_right = (box.upper_right[0] + x_offset, box.upper_right[1] + y_offset)
    return page


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
            result_page = None
            current_page_num = page_num
            while result_page is None:
                page = reader.pages[current_page_num]
                if RotateType.ORIENT in ROTATE_TYPES:
                    page.rotate(random.choice([90, 180, 270]))
                if RotateType.SKEW in ROTATE_TYPES:
                    page = skew_page(page)
                try:
                    writer.add_page(page)
                    result_page = page
                except Exception as e:
                    print(e)
                    current_page_num = random.choice(list(set(range(total_pages)).difference(random_pages)))
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
