

class AttachedFile:

    def __init__(self, original_name: str, tmp_file_path: str):
        """
        Hold information about attached files.
        :param original_name: Name of the file from which the attachments were extracted
        :param tmp_file_path: path to the attachment file.
        """
        self.original_name = original_name
        self.tmp_file_path = tmp_file_path

    def __iter__(self):
        yield self.original_name
        yield self.tmp_file_path
