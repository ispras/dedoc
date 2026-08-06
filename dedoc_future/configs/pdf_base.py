import math

from pydantic import Field, model_validator
from typing_extensions import Self

from dedoc_future.configs.base import BaseProcessorConfig


class PdfBaseConfig(BaseProcessorConfig):
    start_page: int | None = Field(default=None, title="First page of reading page range (counting starts from 1)")
    end_page: int | None = Field(default=None, title="Last page of reading page range (included to the range)")

    @model_validator(mode="after")
    def check_page_range(self) -> Self:
        self.start_page = 0 if self.start_page is None else self.start_page - 1
        self.end_page = math.inf if self.end_page is None else self.end_page

        if self.start_page < 0:
            raise ValueError("`start_page` should be > 0")

        if self.end_page < 0:
            raise ValueError("`end_page` should be > 0")

        if self.start_page > self.end_page:
            raise ValueError("`start_page` should be more than `end_page`")

        return self
