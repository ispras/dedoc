from src.data_structures.attached_file import AttachedFile

from src.readers.scanned_reader.data_classes.tables.location import Location


class PdfImageAttachment(AttachedFile):

    def __init__(self,
                 original_name: str,
                 tmp_file_path: str,
                 need_content_analysis: bool,
                 uid: str,
                 location: Location) -> None:
        self.location = location
        super().__init__(original_name=original_name,
                         tmp_file_path=tmp_file_path,
                         need_content_analysis=need_content_analysis,
                         uid=uid)
