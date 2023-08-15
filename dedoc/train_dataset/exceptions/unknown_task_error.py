from dedoc.train_dataset.exceptions.train_dataset_error import TrainDatasetError


class UnknownTaskError(TrainDatasetError):
    """
    Raise if you try to create dataset with unknown type
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
