from dedoc.data_structures import LinkedTextAnnotation


class BibliographyAnnotation(LinkedTextAnnotation):
    """
    This annotation indicate the place of the bibliography (\\cite) in the original document.
    The line containing this annotation is placed directly before the referred bibliography.
    Example using (example for document_type="article"):
        node:{
            text: "As for the PRF, we use the tree-based construction from Goldreich, Goldwasser and Micali [18]"
            annotations: [{'start': 90, 'end': 92, 'name': 'bibliography_ref', 'value': '97cfac39-f0e3-11ee-b81c-b88584b4e4a1'}, ...],
            ...
        }
        ...
        node:{
            text: "",
            metadata: {
                paragraph_type: "bibliography_item",
                "uid": "97cfac39-f0e3-11ee-b81c-b88584b4e4a1",
                ...
            }
            subparagraphs: [...]
        }
    """
    name = "bibliography_ref"

    def __init__(self, name: str, start: int, end: int) -> None:
        """
        :param name: unique identifier of the table which is referenced inside this annotation
        :param start: start of the annotated text (usually zero)
        :param end: end of the annotated text (usually end of the line)
        """
        super().__init__(start=start, end=end, value=name)
