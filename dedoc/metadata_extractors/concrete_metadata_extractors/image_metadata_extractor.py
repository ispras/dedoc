import math
import os
from typing import Optional, Union

import piexif
from PIL import ExifTags, Image
from dateutil import parser

from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class ImageMetadataExtractor(BaseMetadataExtractor):
    """
    This class is used to extract metadata from images.
    It expands metadata retrieved by :class:`~dedoc.metadata_extractors.BaseMetadataExtractor`.

    In addition to them, the following fields can be added to the metadata other fields:
        - date time, date time digitized, date time original;
        - digital zoom ratio;
        - exif image height, image width and version;
        - light source;
        - make;
        - model;
        - orientation;
        - resolution unit;
        - software;
        - subject distance range;
        - user comment.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.keys = {
            "DateTime": ("date_time", self.__parse_date),
            "DateTimeDigitized": ("date_time_digitized", self.__parse_date),
            "DateTimeOriginal": ("date_time_original", self.__parse_date),
            "DigitalZoomRatio": ("digital_zoom_ratio", self.__parse_float),
            "ExifImageHeight": ("exif_image_height", self.__parse_int),
            "ExifImageWidth": ("exif_image_width", self.__parse_int),
            "ExifVersion": ("exif_version", self.__encode_exif),
            "LightSource": ("light_source", self.__parse_int),
            "Make": ("make", self.__encode_exif),
            "Model": ("model", self.__encode_exif),
            "Orientation": ("orientation", self.__parse_int),
            "ResolutionUnit": ("resolution_unit", self.__parse_int),
            "Software": ("software", self.__encode_exif),
            "SubjectDistanceRange": ("subject_distance_range", self.__parse_int),
            "UserComment": ("user_comment", self.__encode_exif)
        }

    def can_extract(self,
                    file_path: str,
                    converted_filename: Optional[str] = None,
                    original_filename: Optional[str] = None,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        Check if the document has image-like extension (".png", ".jpg", ".jpeg").
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.can_extract` documentation to get the information about parameters.
        """
        file_dir, file_name, converted_filename, original_filename = self._get_names(file_path, converted_filename, original_filename)
        return converted_filename.lower().endswith((".png", ".jpg", ".jpeg"))

    def extract(self,
                file_path: str,
                converted_filename: Optional[str] = None,
                original_filename: Optional[str] = None,
                parameters: Optional[dict] = None,
                other_fields: Optional[dict] = None) -> dict:
        """
        Add the predefined list of metadata for images.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.extract` documentation to get the information about parameters.
        """
        file_dir, file_name, converted_filename, original_filename = self._get_names(file_path, converted_filename, original_filename)
        result = super().extract(file_path=file_path, converted_filename=converted_filename, original_filename=original_filename, parameters=parameters,
                                 other_fields=other_fields)

        path = os.path.join(file_dir, converted_filename)
        exif_fields = self._get_exif(path)
        if len(exif_fields) > 0:
            result["other_fields"] = {**result.get("other_fields", {}), **exif_fields}
        return result

    def __encode_exif(self, exif: Union[str, bytes]) -> Optional[str]:
        if isinstance(exif, bytes):
            try:
                return exif.decode()
            except UnicodeDecodeError:
                return None
        return str(exif)

    def __parse_int(self, exif: Union[str, bytes]) -> Optional[int]:
        try:
            exif = self.__encode_exif(exif)
            return int(exif)
        except Exception:
            return None

    def __parse_date(self, date_str: Union[str, bytes]) -> Optional[int]:
        try:
            date_str = self.__encode_exif(date_str)
            date = parser.parse(date_str.replace(": ", ":"))
            return int(date.timestamp())
        except Exception:
            return None

    def __parse_float(self, exif: Union[str, bytes]) -> Optional[float]:
        try:
            exif = self.__encode_exif(exif)
            result = float(exif)
            return None if math.isnan(result) else result
        except Exception:
            return None

    def _get_exif(self, path: str) -> dict:
        try:
            image = Image.open(path)
            exif_dict = piexif.load(image.info["exif"]).get("Exif", {}) if "exif" in image.info else {}
            exif = {ExifTags.TAGS[k]: v for k, v in exif_dict.items() if k in ExifTags.TAGS}
            encoded_dict = {key_renamed: encode_function(exif.get(key)) for key, (key_renamed, encode_function) in self.keys.items() if key in exif}
            encoded_dict = {k: v for k, v in encoded_dict.items() if k is not None if v is not None}
            image.close()
            return encoded_dict
        except Exception as e:  # noqa
            self.logger.debug(e)
            return {"broken_image": True}
