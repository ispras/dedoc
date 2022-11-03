from typing import TypeVar, Optional
from weakref import WeakSet

from flask_restx import fields

T = TypeVar("T")


class AnyNotNullField(fields.Raw):
    __schema_type__ = 'any'

    def format(self, value: T) -> Optional[T]:  # NOQA
        if not isinstance(value, WeakSet):
            return value


class ForbiddenField(fields.Raw):
    __schema_type__ = 'any'

    def format(self, value: T) -> None:  # NOQA
        return


# ==================== Wildcard fields =======================

wild_any_fields = fields.Wildcard(AnyNotNullField, description="other fields", skip_none=False, allow_null=False)
wild_forbid_fields = fields.Wildcard(ForbiddenField, description="forbidden fields for output")
