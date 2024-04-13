from dedoc.data_structures.annotation import Annotation


class ReferenceAnnotation(Annotation):
    """
    This annotation points to a place in the document text that is a link to another node in the document (for example, another text node).

    Example using (example for document_type="article" with the example of link on the bibliography_item :class:`~dedoc.data_structures.LineWithMeta`) ::

        LineWithMeta:
            LineWithMeta(   // the line with the reference annotation
            line="As for the PRF, we use the tree-based construction from Goldreich, Goldwasser and Micali [18]",
            metadata=LineMetadata(page_id=0, line_id=32),
            annotations=[ReferenceAnnotation(start=90, end=92, value='97cfac39-f0e3-11ee-b81c-b88584b4e4a1'), ...]),
        ...
        other LineWithMeta 's
        ...
        LineWithMeta:
            LineWithMeta(   // The line referenced by the previous one
            line="your some text (can be empty)",
            metadata=LineMetadata(page_id=10,
                                  line_id=189,
                                  tag_hierarchy_level=HierarchyLevel(level1=2, level2=0, paragraph_type="bibliography_item")),
                                  other_fields={"uid": '97cfac39-f0e3-11ee-b81c-b88584b4e4a1'})
            annotations=[])
    """
    name = "reference"

    def __init__(self, value: str, start: int, end: int) -> None:
        """
        :param value: unique identifier of the line to which this annotation refers
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        """
        super().__init__(start=start, end=end, name=self.name, value=value, is_mergeable=False)
