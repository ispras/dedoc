from abc import ABCMeta, abstractmethod

import numpy as np
from immutabledict import immutabledict
from tdm.abstract.datamodel import AbstractMarkup
from tdm.wrapper.node import modifier
from typing_extensions import Self


class AbstractPdfPageMarkup(metaclass=ABCMeta):
    @property
    @abstractmethod
    def image(self) -> np.ndarray | None:
        pass

    @property
    @abstractmethod
    def orig_image(self) -> np.ndarray | None:
        pass

    @property
    @abstractmethod
    def angle(self) -> float | None:
        pass

    @property
    @abstractmethod
    def text_layer(self) -> bool | None:
        pass

    @modifier
    @abstractmethod
    def set_image(self, image: np.ndarray) -> Self:
        pass

    @modifier
    @abstractmethod
    def set_orig_image(self, orig_image: np.ndarray) -> Self:
        pass

    @modifier
    @abstractmethod
    def set_angle(self, angle: float) -> Self:
        pass

    @modifier
    @abstractmethod
    def set_text_layer(self, text_layer: bool) -> Self:
        pass


class PdfPageMarkup(AbstractMarkup, AbstractPdfPageMarkup):
    def __init__(
            self, image: np.ndarray | None = None, orig_image: np.ndarray | None = None, angle: float | None = None, text_layer: bool | None = None
    ) -> None:
        self._image = image if image is not None else orig_image
        self._orig_image = orig_image
        self._angle = angle
        self._text_layer = text_layer

    @property
    def markup(self) -> immutabledict:
        res_dict = {}

        if self._image is not None:
            res_dict["image"] = self._image

        if self._orig_image is not None:
            res_dict["orig_image"] = self._orig_image

        if self._angle is not None:
            res_dict["angle"] = self._angle

        if self._text_layer is not None:
            res_dict["text_layer"] = self._text_layer

        return immutabledict(res_dict)

    @classmethod
    def from_markup(cls, markup: AbstractMarkup) -> Self:
        markup_dict = markup.markup
        return cls(
            image=markup_dict.get("image"),
            orig_image=markup_dict.get("orig_image"),
            angle=markup_dict.get("angle"),
            text_layer=markup_dict.get("text_layer")
        )

    @property
    def image(self) -> np.ndarray | None:
        return self._image

    @property
    def orig_image(self) -> np.ndarray | None:
        return self._orig_image

    @property
    def angle(self) -> float | None:
        return self._angle

    @property
    def text_layer(self) -> bool | None:
        return self._text_layer

    def set_image(self, image: np.ndarray) -> Self:
        return PdfPageMarkup(image=image, orig_image=self._orig_image, angle=self._angle, text_layer=self._text_layer)

    def set_orig_image(self, orig_image: np.ndarray) -> Self:
        if self._orig_image is not None:
            raise ValueError("orig_image is already set")

        image = orig_image if self._image is None else self._image

        return PdfPageMarkup(image=image, orig_image=orig_image, angle=self._angle, text_layer=self._text_layer)

    def set_angle(self, angle: float) -> Self:
        return PdfPageMarkup(image=self._image, orig_image=self._orig_image, angle=angle, text_layer=self._text_layer)

    def set_text_layer(self, text_layer: bool) -> Self:
        return PdfPageMarkup(image=self._image, orig_image=self._orig_image, angle=self._angle, text_layer=text_layer)
