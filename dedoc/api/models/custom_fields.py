from flask_restplus import fields
from weakref import WeakSet


class AnyNotNullField(fields.Raw):
    __schema_type__ = 'any'

    def format(self, value):
        if not isinstance(value, WeakSet):
            return value


class ForbiddenField(fields.Raw):
    __schema_type__ = 'any'

    def format(self, value):
        return


# ==================== Wildcard fields =======================

wild_any_fields = fields.Wildcard(AnyNotNullField, description="other fields", skip_none=False, allow_null=False)
wild_forbid_fields = fields.Wildcard(ForbiddenField, description="forbidden fields for output")
