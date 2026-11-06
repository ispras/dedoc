# TODO
from __future__ import annotations

from typing import Any

from pydantic import Field, ValidationError

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules import AbstractModule
from dedoc_future.errors.config import RuntimeConfigError


class RuntimeConfig(ImmutableBaseModel):
    """
    - Automatically collect processors configs and make common schema TODO in system config
    - Common params (global)
    - Get localized processors configs (local)
    """
    global_params: dict[str, Any] = Field(default_factory=dict)  # TODO pydantic
    module_params: dict[str, dict[str, Any]] = Field(default_factory=dict)

    def get_for(self, module: AbstractModule) -> ImmutableBaseModel:
        schema = module.runtime_schema()

        merged: dict[str, Any] = {}

        for fname in schema.model_fields:
            if fname in self.global_params:
                merged[fname] = self.global_params[fname]

        local = self.module_params.get(module.name(), {})
        unknown = set(local) - set(schema.model_fields)
        if unknown:
            raise RuntimeConfigError(
                f"{module.name()}: unknown params {sorted(unknown)}; "
                f"schema fields: {sorted(schema.model_fields)}"
            )
        merged.update(local)

        try:
            return schema.model_validate(**merged)
        except ValidationError as exc:
            raise RuntimeConfigError(f"{module.name()}: invalid params: {exc}") from exc
