import os

import torch
from sage.spelling_correction import AvailableCorrectors
from sage.spelling_correction import RuM2M100ModelForSpellingCorrection


"""
Install sage library (for ocr correction step):
git clone https://github.com/ai-forever/sage.git
cd sage
pip install .
pip install -r requirements.txt

Note: sage use 5.2 Gb GPU ......
"""


class SageCorrector:

    def __init__(self, cache_dir: str, use_gpu: bool = True) -> None:
        self.corrected_path = os.path.join(cache_dir, "result_corrected")
        os.makedirs(self.corrected_path, exist_ok=True)

        self.corrector = RuM2M100ModelForSpellingCorrection.from_pretrained(AvailableCorrectors.m2m100_1B.value)  # 4.49 Gb model (pytorch_model.bin)
        self._init_device(use_gpu)

    def _init_device(self, use_gpu: bool) -> None:
        if torch.cuda.is_available() and use_gpu:
            self.corrector.model.to(torch.device("cuda:0"))
            print("use CUDA")
        else:
            print("use CPU")

    def correction(self, text: str) -> str:
        corrected_lines = []
        for line in text.split("\n"):
            corrected_lines.append(self.corrector.correct(line)[0])
        corrected_text = "\n".join(corrected_lines)

        return corrected_text
