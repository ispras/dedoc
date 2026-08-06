from os import PathLike

from pydantic import BaseModel, Field


class BaseProcessorConfig(BaseModel):
    with_attachments: bool = Field(default=False, title="Enable attached files extraction")
    attachments_dir: PathLike | None = Field(default=None, title="Path to directory for attached files saving")
