import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Set, Tuple

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils.parameter_utils import get_param_attachments_dir
from dedoc.utils.utils import get_mime_extension, save_data_to_unique_file


class AbstractAttachmentsExtractor(ABC):
    """
    This class is responsible for extracting files attached to the documents of different formats.
    """
    def __init__(self, *, config: Optional[dict] = None, recognized_extensions: Optional[Set[str]] = None, recognized_mimes: Optional[Set[str]] = None) -> None:
        """
        :param config: configuration of the attachments extractor, e.g. logger for logging
        :param recognized_extensions: set of supported files extensions with a dot, for example {.doc, .pdf}
        :param recognized_mimes: set of supported MIME types of files
        """
        self.config = {} if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())
        self._recognized_extensions = {} if recognized_extensions is None else recognized_extensions
        self._recognized_mimes = {} if recognized_mimes is None else recognized_mimes

    def can_extract(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        """
        Check if this attachments extractor can get attachments of the file.
        You should provide at least one of the following parameters: file_path, extension, mime.

        :param file_path: the path of the file to extract attachments from
        :param extension: file extension with a dot, for example .doc or .pdf
        :param mime: MIME type of file
        :param parameters: any additional parameters for the given document
        :return: the indicator of possibility to get attachments of this file
        """
        mime, extension = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in self._recognized_extensions or mime in self._recognized_mimes

    @abstractmethod
    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Extract attachments from the given file.
        This method can only be called on appropriate files, ensure that \
        :meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor.can_extract` is True for the given file.

        :param file_path: path of the file to extract attachments from
        :param parameters: dict with different parameters for extracting, see :ref:`attachments_handling_parameters` for more details
        :return: list of file's attachments
        """
        pass

    @staticmethod
    def with_attachments(parameters: dict) -> bool:
        """
        Check if the option `with_attachments` is true in the parameters.

        :param parameters: parameters for the attachment extractor
        :return: indicator if with_attachments option is true
        """
        return str(parameters.get("with_attachments", "false")).lower() == "true"

    def _content2attach_file(self, content: List[Tuple[str, bytes]], tmpdir: str, need_content_analysis: bool, parameters: dict) -> List[AttachedFile]:
        attachments = []
        attachments_dir = get_param_attachments_dir(parameters, tmpdir)

        for original_name, contents in content:
            tmp_file_name = save_data_to_unique_file(directory=attachments_dir, filename=original_name, binary_data=contents)
            tmp_file_path = os.path.join(attachments_dir, tmp_file_name)
            file = AttachedFile(original_name=original_name,
                                tmp_file_path=tmp_file_path,
                                uid=f"attach_{uuid.uuid4()}",
                                need_content_analysis=need_content_analysis)
            attachments.append(file)
        return attachments
