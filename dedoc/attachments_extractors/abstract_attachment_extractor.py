import os
import uuid
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils.utils import save_data_to_unique_file


class AbstractAttachmentsExtractor(ABC):
    """
    This class is responsible for extracting files attached to the documents of different formats.
    """

    @abstractmethod
    def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Check if this attachments extractor can get attachments of the file with the given extension.

        :param extension: file extension, for example .doc or .pdf
        :param mime: MIME type of file
        :param parameters: any additional parameters for given document
        :return: the indicator of possibility to get attachments of this file
        """
        pass

    @abstractmethod
    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Extract attachments from the given file.
        This method can only be called on appropriate files, ensure that \
        :meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor.can_extract` is True for the given file.

        :param tmpdir: directory where file is located and where the attached files will be saved
        :param filename: name of the file to extract attachments (not absolute path)
        :param parameters: dict with different parameters for extracting
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

    def _content2attach_file(self,
                             content: List[Tuple[str, bytes]],
                             tmpdir: str,
                             need_content_analysis: bool) -> List[AttachedFile]:
        attachments = []
        for original_name, contents in content:
            tmp_file_name = save_data_to_unique_file(directory=tmpdir, filename=original_name, binary_data=contents)
            tmp_file_path = os.path.join(tmpdir, tmp_file_name)
            file = AttachedFile(original_name=original_name,
                                tmp_file_path=tmp_file_path,
                                uid=f"attach_{uuid.uuid1()}",
                                need_content_analysis=need_content_analysis)
            attachments.append(file)
        return attachments
