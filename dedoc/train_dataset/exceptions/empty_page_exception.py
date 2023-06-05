from dedoc.train_dataset.exceptions.train_dataset_exception import TrainDatasetException


class EmptyPageException(TrainDatasetException):

    def __init__(self, message: str) -> None:
        super().__init__(message)
