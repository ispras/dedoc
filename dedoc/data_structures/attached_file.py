class AttachedFile:
    """
    Holds information about files, attached to the parsed document.

    :ivar original_name: original name of the attached file if it was possible to extract it
    :ivar tmp_file_path: path to the attached file on disk - its name is different from original_name
    :ivar need_content_analysis: does the attached file need parsing (enable recursive parsing in :class:`~dedoc.DedocManager`)
    :ivar uid: unique identifier of the attached file

    :vartype original_name: str
    :vartype tmp_file_path: str
    :vartype need_content_analysis: bool
    :vartype uid: str
    """
    def __init__(self, original_name: str, tmp_file_path: str, need_content_analysis: bool, uid: str) -> None:
        """
        :param original_name: original name of the attached file
        :param tmp_file_path: path to the attachment file
        :param need_content_analysis: indicator should we parse the attachment's content or simply save it without parsing
        :param uid: unique identifier of the attachment
        """
        self.original_name: str = original_name
        self.tmp_file_path: str = tmp_file_path
        self.need_content_analysis: bool = need_content_analysis
        self.uid: str = uid

    def get_filename_in_path(self) -> str:
        return self.tmp_file_path

    def get_original_filename(self) -> str:
        return self.original_name
