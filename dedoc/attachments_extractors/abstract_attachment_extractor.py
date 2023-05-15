import os
import uuid
from abc import ABC, abstractmethod
from typing import List, Tuple

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.utils.utils import save_data_to_unique_file


class AbstractAttachmentsExtractor(ABC):
    """
    AbstractAttachmentsExtractor is responsible for extracting attached files from PDF or docx file types
    """

    @abstractmethod
    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        """
        Extract attachments from given file.
        This method can only be called on appropriate files,
        ensure that `can_extract` is True for given file.
        :param tmpdir: directory where file is located.
        :param filename: Name of the file from which you should extract attachments (not abs path, only file name, use
        os.path.join(tmpdir, filename) to obtain path)
        :param parameters: dict with different parameters for extracting
        You can be sure that the file name consists only of letters
        numbers and dots.
        :return: List[[attacment_name, attachment_byte]] - list of attachment name file and
                containing of attachment file in bytes
        """
        pass

    @staticmethod
    def with_attachments(parameters: dict) -> bool:
        return str(parameters.get("with_attachments", "false")).lower() == "true"

    def _content2attach_file(self,
                             content: List[Tuple[str, bytes]],
                             tmpdir: str,
                             need_content_analysis: bool) -> List[AttachedFile]:
        attachments = []
        for original_name, contents in content:
            tmp_file_name = save_data_to_unique_file(directory=tmpdir,
                                                     filename=original_name,
                                                     binary_data=contents)
            tmp_file_path = os.path.join(tmpdir, tmp_file_name)
            file = AttachedFile(original_name=original_name,
                                tmp_file_path=tmp_file_path,
                                uid="attach_{}".format(uuid.uuid1()),
                                need_content_analysis=need_content_analysis)
            attachments.append(file)
        return attachments
