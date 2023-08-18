from dedoc.train_dataset.exceptions.train_dataset_error import TrainDatasetError


class EmptyPageError(TrainDatasetError):

    def __init__(self, message: str) -> None:
        super().__init__(message)
