class AttachedFile:

    def __init__(self, original_name: str, tmp_file_path: str, need_content_analysis: bool, uid: str) -> None:
        """
        Holds information about attached files.
        :param original_name: Name of the file from which the attachments are extracted
        :param tmp_file_path: path to the attachment file.
        """
        self.original_name = original_name
        self.tmp_file_path = tmp_file_path
        self.need_content_analysis = need_content_analysis
        self.uid = uid

    def get_filename_in_path(self) -> str:
        return self.tmp_file_path

    def get_original_filename(self) -> str:
        return self.original_name
