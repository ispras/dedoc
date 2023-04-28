

class MinioException(Exception):

    def __init__(self, message: str, status_code: int, *args: object) -> None:
        super().__init__(*args)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        return f"MinioException({self.status_code}, {self.message})"

    def __repr__(self) -> str:
        return str(self)
