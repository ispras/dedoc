from typing import Any, Optional

from fastapi import Body

from dedoc.api.api_args import QueryParameters


class TrainDatasetParameters(QueryParameters):
    type_of_task: Optional[str]
    task_size: Optional[str]

    def __init__(self,
                 type_of_task: Optional[str] = Body(description="Type of the task to create", default=None),
                 task_size: Optional[str] = Body(description="Maximum number of images in one task", default=None),

                 document_type: Optional[str] = Body(default=None),
                 pdf_with_text_layer: Optional[str] = Body(default=None),
                 language: Optional[str] = Body(default=None),
                 need_header_footer_analysis: Optional[str] = Body(default=None),

                 **data: Any) -> None:

        super().__init__(**data)
        self.type_of_task: str = type_of_task or ""
        self.task_size: str = task_size or "250"

        self.document_type = document_type or ""
        self.pdf_with_text_layer = pdf_with_text_layer or 'auto'
        self.language = language or "rus+eng"
        self.need_header_footer_analysis = need_header_footer_analysis or 'false'
