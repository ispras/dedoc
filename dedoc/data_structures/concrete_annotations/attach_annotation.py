from dedoc.data_structures.annotation import Annotation


class AttachAnnotation(Annotation):
    """
    This annotation indicate the place of the attachment in the original document (for example, the place where image
    was placed in the docx document).
    The line containing this annotation is placed directly before the referred attachment.
    """
    name = "attachment"

    def __init__(self, attach_uid: str, start: int, end: int) -> None:
        """
        :param attach_uid: unique identifier of the attachment which is referenced inside this annotation
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        """
        super().__init__(start=start, end=end, name=AttachAnnotation.name, value=attach_uid, is_mergeable=False)
