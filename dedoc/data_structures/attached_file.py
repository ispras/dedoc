class AttachedFile:
    """
    Holds information about files, attached to the parsed document.
    """
    def __init__(self, original_name: str, tmp_file_path: str, need_content_analysis: bool, uid: str) -> None:
        """
        :param original_name: Name of the file from which the attachments are extracted
        :param tmp_file_path: path to the attachment file.
        :param need_content_analysis: indicator should we parse the attachment's content or simply save it without parsing
        :param uid: unique identifier of the attachment
        """
        self.original_name = original_name
        self.tmp_file_path = tmp_file_path
        self.need_content_analysis = need_content_analysis
        self.uid = uid

    def get_filename_in_path(self) -> str:
        return self.tmp_file_path

    def get_original_filename(self) -> str:
        return self.original_name
