from typing import Any

from pydantic import Field, model_validator

from dedoc_future.configs.base import BaseProcessorConfig


class PdfBaseConfig(BaseProcessorConfig):
    start_page: int | None = Field(default=None, title="First page of reading page range (counting starts from 1)")
    end_page: int | None = Field(default=None, title="Last page of reading page range (included to the range)")

    @model_validator(mode="before")
    @classmethod
    def check_page_range(cls, data: Any) -> Any:  # noqa ANN401
        if not isinstance(data, dict):
            return data

        start_page: int | None = data.get("start_page")
        end_page: int | None = data.get("end_page")
        start_page = 0 if start_page is None else start_page - 1
        end_page = 10 ** 10 if end_page is None else end_page

        if start_page < 0:
            raise ValueError("`start_page` should be > 0")

        if end_page <= 0:
            raise ValueError("`end_page` should be > 0")

        if start_page >= end_page:
            raise ValueError("`start_page` should be more than `end_page`")

        data["start_page"] = start_page
        data["end_page"] = end_page

        return data
