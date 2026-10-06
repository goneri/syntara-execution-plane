"""SQLModel types used by the execution-plane persistence models."""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter
from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect
    from sqlalchemy.types import TypeEngine


class UUIDListJSONB(TypeDecorator):  # type: ignore[type-arg]
    """Store UUID lists as JSON strings and restore UUID objects on reads."""

    impl = JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        """Use SQL NULL for Python ``None`` instead of JSON ``null``."""
        return dialect.type_descriptor(JSONB(none_as_null=True))

    def process_bind_param(self, value: object, _dialect: Dialect) -> list[str] | None:
        """Convert UUID objects or strings to JSON-compatible UUID strings."""
        if value is None:
            return None
        if not isinstance(value, list):
            error_message = "Project IDs must be a list of UUIDs or None"
            raise TypeError(error_message)
        try:
            return [str(uuid.UUID(str(item))) for item in value]
        except (AttributeError, TypeError, ValueError) as error:
            error_message = "Project IDs must contain only valid UUIDs"
            raise ValueError(error_message) from error

    def process_result_value(self, value: object, _dialect: Dialect) -> list[uuid.UUID] | None:
        """Restore JSON UUID strings to UUID objects; normalize JSON null."""
        if value is None:
            return None
        if not isinstance(value, list):
            error_message = "Stored project IDs must be a JSON array or null"
            raise TypeError(error_message)
        try:
            return [uuid.UUID(str(item)) for item in value]
        except (AttributeError, TypeError, ValueError) as error:
            error_message = "Stored project IDs contain an invalid UUID"
            raise ValueError(error_message) from error


class DiscriminatedJSONB(TypeDecorator):  # type: ignore[type-arg]
    """Store and restore a Pydantic discriminated union in a JSONB column."""

    impl = JSONB
    cache_ok = True

    def __init__(self, union_type: type, *args: object, **kwargs: object) -> None:
        """Initialize the type adapter for the discriminated union."""
        super().__init__(*args, **kwargs)
        self.type_adapter: TypeAdapter[Any] = TypeAdapter(union_type)

    def process_bind_param(self, value: object, _dialect: Dialect) -> object:
        """Convert a model or JSON-compatible value for database storage."""
        if value is None:
            return None

        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return value

        try:
            return json.loads(json.dumps(value))
        except (TypeError, ValueError) as error:
            type_name = type(value).__name__
            error_message = f"Cannot serialize value of type '{type_name}' to JSON"
            raise ValueError(error_message) from error

    def process_result_value(self, value: object, _dialect: Dialect) -> object:
        """Convert a JSON object from the database to its concrete model."""
        if value is None or not isinstance(value, dict):
            return value

        try:
            return self.type_adapter.validate_python(value)
        except (TypeError, ValueError):
            return value
