from typing import List, Optional, Tuple

from pypdf import PdfReader

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.data_structures.attached_file import AttachedFile


class PDFAttachmentsExtractor(AbstractAttachmentsExtractor):
    """
    Extract attachments from pdf files.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes
        super().__init__(config=config, recognized_extensions=recognized_extensions.pdf_like_format, recognized_mimes=recognized_mimes.pdf_like_format)

    def extract(self, file_path: str, parameters: Optional[dict] = None) -> List[AttachedFile]:
        """
        Get attachments from the given pdf document.

        Look to the :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor` documentation to get the information about \
        the methods' parameters.
        """
        import os
        from dedoc.utils.parameter_utils import get_param_attachments_dir, get_param_need_content_analysis
        from pypdf.errors import PdfReadError

        parameters = {} if parameters is None else parameters
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as handler:
            try:
                reader = PdfReader(handler)
            except Exception as e:
                self.logger.warning(f"can't handle {filename}, get {e}")
                return []
            attachments = []
            try:
                attachments.extend(self.__get_root_attachments(reader))
            except PdfReadError:
                self.logger.warning(f"{filename} is broken")
            try:
                attachments.extend(self.__get_page_level_attachments(reader))
            except PdfReadError:
                self.logger.warning(f"{filename} is broken")

        need_content_analysis = get_param_need_content_analysis(parameters)
        attachments_dir = get_param_attachments_dir(parameters, file_path)
        return self._content2attach_file(content=attachments, tmpdir=attachments_dir, need_content_analysis=need_content_analysis, parameters=parameters)

    def __get_page_level_attachments(self, reader: PdfReader) -> List[Tuple[str, bytes]]:
        attachments = []
        for page in reader.pages:
            for annot in page.get("/Annots", []):
                subtype = annot.get_object().get("/Subtype")
                if subtype == "/FileAttachment":
                    obj = annot.get_object()
                    name = obj["/FS"]["/UF"]
                    data = obj["/FS"]["/EF"]["/F"].get_data()  # The file containing the stream data.
                    attachments.append([name, data])

        return attachments

    def __get_root_attachments(self, reader: PdfReader) -> List[Tuple[str, bytes]]:
        """
        Retrieves the file attachments of the PDF as a dictionary of file names and the file data as a bytestring.

        :return: dictionary of filenames and bytestrings
        """
        import uuid

        attachments = []
        catalog = reader.trailer.get("/Root")
        if catalog is None:
            return attachments

        if "/Names" in catalog.keys() and "/EmbeddedFiles" in catalog["/Names"].keys() and "/Names" in catalog["/Names"]["/EmbeddedFiles"].keys():
            file_names = catalog["/Names"]["/EmbeddedFiles"]["/Names"]
            for f in file_names:
                if isinstance(f, str):
                    data_index = file_names.index(f) + 1
                    dict_object = file_names[data_index].get_object()
                    if "/EF" in dict_object and "/F" in dict_object["/EF"]:
                        data = dict_object["/EF"]["/F"].get_data()
                        name = dict_object.get("/UF", f"pdf_attach_{uuid.uuid4()}")
                        attachments.append((name, data))

        return attachments
