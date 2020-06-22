import os
import zipfile
from typing import List

from dedoc.attachments_extractors.base_attachments_extractor import BaseAttachmentsExtractor
from dedoc.utils import splitext_


class ExcelAttachmentsExtractor(BaseAttachmentsExtractor):

    def get_attachments(self, tmpdir: str, filename: str) -> List[List]:
        attachments = []
        name, ext = splitext_(filename)
        if ext == '.xlsx':

            with zipfile.ZipFile(os.path.join(tmpdir, filename), 'r') as zfile:
                name_zip, *files = zfile.namelist()
                print(name_zip)

                medias = [file for file in files if file.startswith("xl/media/")]

                for media in medias:
                    namefile = os.path.split(media)[-1]
                    attachments.append([namefile, zfile.read(media)])

        return attachments
