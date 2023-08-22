from typing import Optional, TypeVar
from weakref import WeakSet

from flask_restx import fields

T = TypeVar("T")


class AnyNotNullField(fields.Raw):
    __schema_type__ = "any"

    def format(self, value: T) -> Optional[T]:  # noqa
        if not isinstance(value, WeakSet):
            return value


class ForbiddenField(fields.Raw):
    __schema_type__ = "any"

    def format(self, value: T) -> None:  # noqa
        return


# ==================== Wildcard fields =======================

wild_any_fields = fields.Wildcard(AnyNotNullField, description="other fields", skip_none=False, allow_null=False)
wild_forbid_fields = fields.Wildcard(ForbiddenField, description="forbidden fields for output")
