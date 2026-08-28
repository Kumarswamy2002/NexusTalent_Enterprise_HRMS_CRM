"""
NexusTalent Dynamic Schema & Custom Fields Engine
Allows Tenants & HR Admins to attach custom typed metadata (e.g. T-shirt size, Visa status, Custom scores)
without altering PostgreSQL / SQLite schemas.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import re


class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    JSON = "json"


class CustomFieldDefinition(BaseModel):
    name: str
    label: str
    field_type: FieldType
    is_required: bool = False
    default_value: Optional[Any] = None
    options: Optional[List[str]] = None  # For select/multi_select
    validation_regex: Optional[str] = None
    description: Optional[str] = None


class DynamicFieldEngine:
    """Validates and cleanses custom field payloads according to tenant schema definitions."""

    @classmethod
    def validate_and_sanitize(
        cls,
        definitions: List[CustomFieldDefinition],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        def_map = {d.name: d for d in definitions}

        # Check required fields
        for d in definitions:
            if d.is_required and (d.name not in data or data[d.name] is None):
                raise ValueError(f"Custom field '{d.label}' ({d.name}) is required.")

        for key, value in data.items():
            if key not in def_map:
                # Store unvalidated extra attribute
                cleaned[key] = value
                continue

            field_def = def_map[key]
            if value is None:
                cleaned[key] = field_def.default_value
                continue

            # Type validations
            if field_def.field_type == FieldType.NUMBER:
                try:
                    cleaned[key] = float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Field '{field_def.label}' must be a valid number.")

            elif field_def.field_type == FieldType.BOOLEAN:
                if isinstance(value, bool):
                    cleaned[key] = value
                elif str(value).lower() in ("true", "1", "yes"):
                    cleaned[key] = True
                elif str(value).lower() in ("false", "0", "no"):
                    cleaned[key] = False
                else:
                    raise ValueError(f"Field '{field_def.label}' must be boolean (true/false).")

            elif field_def.field_type == FieldType.SELECT:
                if field_def.options and value not in field_def.options:
                    raise ValueError(
                        f"Field '{field_def.label}' value '{value}' is not in allowed options: {field_def.options}"
                    )
                cleaned[key] = str(value)

            elif field_def.field_type == FieldType.STRING:
                val_str = str(value)
                if field_def.validation_regex:
                    if not re.match(field_def.validation_regex, val_str):
                        raise ValueError(f"Field '{field_def.label}' does not match required format pattern.")
                cleaned[key] = val_str

            else:
                cleaned[key] = value

        return cleaned
