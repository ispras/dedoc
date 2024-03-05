import os
from typing import Tuple

import torch
from sage.spelling_correction import AvailableCorrectors
from sage.spelling_correction import RuM2M100ModelForSpellingCorrection
from sage.spelling_correction.corrector import Corrector

"""
Install sage library (for ocr correction step):
git clone https://github.com/ai-forever/sage.git
cd sage
pip install .
pip install -r requirements.txt

Note: sage use 5.2 Gb GPU ......
"""
USE_GPU = True


def correction(model: Corrector, ocr_text: str) -> str:

    corrected_lines = []
    for line in ocr_text.split("\n"):
        corrected_lines.append(model.correct(line)[0])
    corrected_text = "\n".join(corrected_lines)

    return corrected_text


def init_correction_step(cache_dir: str) -> Tuple[Corrector, str]:

    corrected_path = os.path.join(cache_dir, "result_corrected")
    os.makedirs(corrected_path, exist_ok=True)
    corrector = RuM2M100ModelForSpellingCorrection.from_pretrained(AvailableCorrectors.m2m100_1B.value)  # 4.49 Gb model (pytorch_model.bin)
    if torch.cuda.is_available() and USE_GPU:
        corrector.model.to(torch.device("cuda:0"))
        print("use CUDA")
    else:
        print("use CPU")
    return corrector, corrected_path
