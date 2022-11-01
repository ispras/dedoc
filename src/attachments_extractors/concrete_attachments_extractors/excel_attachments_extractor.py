import os
import zipfile
from typing import List

from src.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from src.data_structures.attached_file import AttachedFile
from src.utils.utils import splitext_


class ExcelAttachmentsExtractor(AbstractAttachmentsExtractor):
    """
    Extracts attachments from excel files
    """

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
        attachments = []
        name, ext = splitext_(filename)
        if ext == '.xlsx':

            with zipfile.ZipFile(os.path.join(tmpdir, filename), 'r') as zfile:
                name_zip, *files = zfile.namelist()

                medias = [file for file in files if file.startswith("xl/media/")]

                for media in medias:
                    namefile = os.path.split(media)[-1]
                    attachments.append((namefile, zfile.read(media)))
        return self._content2attach_file(content=attachments, tmpdir=tmpdir)
