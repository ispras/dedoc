from os import PathLike

from pydantic import Field

from dedoc_future.abstract.config import ImmutableBaseModel


class BaseProcessorConfig(ImmutableBaseModel):
    with_attachments: bool = Field(default=False, title="Enable attached files extraction")
    attachments_dir: PathLike | None = Field(default=None, title="Path to directory for attached files saving")
