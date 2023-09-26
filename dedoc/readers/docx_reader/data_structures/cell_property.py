

class CellProperty:
    """
    This class holds information about the table cell.
    """
    def __init__(self, colspan: int, rowspan: int, invisible: bool) -> None:
        """
        :param cell: class which should contain the following attributes: colspan, rowspan, invisible.
        """
        self.colspan = colspan
        self.rowspan = rowspan
        self.invisible = invisible
