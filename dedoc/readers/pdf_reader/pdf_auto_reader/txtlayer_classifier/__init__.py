from typing import Dict

from .abstract_txtlayer_classifier import AbstractTxtlayerClassifier
from .letter_txtlayer_classifier import LetterTxtlayerClassifier
from .ml_txtlayer_classifier import MlTxtlayerClassifier
from .simple_txtlayer_classifier import SimpleTxtlayerClassifier


def get_classifiers(config: dict) -> Dict[str, AbstractTxtlayerClassifier]:
    return {
        "ml": MlTxtlayerClassifier(config=config),
        "simple": SimpleTxtlayerClassifier(config=config),
        "letter": LetterTxtlayerClassifier(config=config)
    }
