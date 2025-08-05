import os
from typing import List, Optional, Set

import numpy as np
from langcodes import Language, LanguageTagError

from dedoc.config import get_config
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.abstract_txtlayer_classifier import AbstractTxtlayerClassifier


class LanguageTxtlayerClassifier(AbstractTxtlayerClassifier):
    """
    Simple multilingual textual layer correctness classification.

    * If language is not in parameters: the textual layer is considered as a correct if its language was detected with probability > 50%.
    * If language is in parameters: the textual layer is considered as a correct if predicted language is in parameters.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.path = os.path.join(get_config()["resources_path"], "language_detector.bin")
        self.__model = None

    @property
    def model(self):  # noqa
        if self.__model is not None:
            return self.__model

        if not os.path.isfile(self.path):
            out_dir, out_name = os.path.split(self.path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="language_detector", hub_name="language_detector.bin")

        assert os.path.isfile(self.path)

        import fasttext
        self.__model = fasttext.load_model(self.path)
        return self.__model

    def predict(self, lines: List[List[LineWithMeta]], parameters: Optional[dict] = None) -> np.ndarray:
        target_languages = self._get_target_languages(parameters)
        texts = np.array([" ".join(line.line for line in line_list).replace("\n", " ") for line_list in lines])
        result = np.array([bool(text.strip()) for text in texts])
        ids_for_pred = np.where(result)[0]
        texts = texts[ids_for_pred]

        if target_languages:
            predictions = self.model.predict(texts.tolist(), k=2)
            predicted_languages = [set(lang.replace("__label__", "") for lang in prediction) for prediction in predictions[0]]
            result[ids_for_pred] = [bool(target_languages.intersection(pred)) for pred in predicted_languages]
        else:
            predictions = self.model.predict(texts.tolist(), threshold=0.5)
            result[ids_for_pred] = [any(pred) for pred in predictions[1]]
        return result

    def _get_target_languages(self, parameters: Optional[dict] = None) -> Set[str]:
        parameters = parameters or {}
        target_language = parameters.get("language")
        target_languages = []
        if target_language and isinstance(target_language, str):
            languages = target_language.lower().split("+")
            for language in languages:
                try:
                    target_languages.append(Language.get(language).language)
                except LanguageTagError:
                    pass
        target_languages = set(target_languages)
        return target_languages
