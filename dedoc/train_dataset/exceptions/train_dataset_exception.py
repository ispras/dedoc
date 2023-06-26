class TrainDatasetException(Exception):
    """
    Raise if there is some problem with completing new train dataset.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
