from pydantic import BaseModel, ConfigDict


class ImmutableBaseModel(BaseModel):
    model_config = ConfigDict(frozen=True)
