# app/utils/validation.py
"""
Input Validation

This module provides schema-based request validation with type checking,
required field validation, length limits, and format validation.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

from flask import request, current_app

from app.utils.errors import ValidationError


T = TypeVar("T")


@dataclass
class FieldValidator:
    """Validator for a single field."""

    name: str
    field_type: Type = str
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    allowed_values: Optional[Set[Any]] = None
    custom_validator: Optional[Callable[[Any], bool]] = None
    custom_error: Optional[str] = None
    strip_whitespace: bool = True
    lowercase: bool = False
    default: Any = None

    def validate(self, value: Any) -> Any:
        """
        Validate and transform a value.

        Args:
            value: The value to validate

        Returns:
            The validated and transformed value

        Raises:
            ValidationError: If validation fails
        """
        # Handle missing/None values
        if value is None or (isinstance(value, str) and not value.strip()):
            if self.required:
                raise ValidationError(
                    message=f"{self.name} is required",
                    field=self.name,
                )
            return self.default

        # Type coercion and transformation
        try:
            if self.field_type == str:
                value = str(value)
                if self.strip_whitespace:
                    value = value.strip()
                if self.lowercase:
                    value = value.lower()
            elif self.field_type == int:
                value = int(value)
            elif self.field_type == float:
                value = float(value)
            elif self.field_type == bool:
                if isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes", "on")
                else:
                    value = bool(value)
            elif self.field_type == list:
                if not isinstance(value, list):
                    raise ValidationError(
                        message=f"{self.name} must be a list",
                        field=self.name,
                    )
            elif self.field_type == dict:
                if not isinstance(value, dict):
                    raise ValidationError(
                        message=f"{self.name} must be an object",
                        field=self.name,
                    )
        except (ValueError, TypeError):
            raise ValidationError(
                message=f"{self.name} must be a valid {self.field_type.__name__}",
                field=self.name,
            )

        # String length validation
        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                raise ValidationError(
                    message=f"{self.name} must be at least {self.min_length} characters",
                    field=self.name,
                    details={"min_length": self.min_length, "actual_length": len(value)},
                )
            if self.max_length is not None and len(value) > self.max_length:
                raise ValidationError(
                    message=f"{self.name} must be at most {self.max_length} characters",
                    field=self.name,
                    details={"max_length": self.max_length, "actual_length": len(value)},
                )

        # Numeric range validation
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(
                    message=f"{self.name} must be at least {self.min_value}",
                    field=self.name,
                )
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(
                    message=f"{self.name} must be at most {self.max_value}",
                    field=self.name,
                )

        # Pattern validation
        if self.pattern is not None and isinstance(value, str):
            if not re.match(self.pattern, value):
                raise ValidationError(
                    message=self.custom_error or f"{self.name} has an invalid format",
                    field=self.name,
                )

        # Allowed values validation
        if self.allowed_values is not None:
            if value not in self.allowed_values:
                raise ValidationError(
                    message=f"{self.name} must be one of: {', '.join(str(v) for v in self.allowed_values)}",
                    field=self.name,
                    details={"allowed_values": list(self.allowed_values)},
                )

        # Custom validation
        if self.custom_validator is not None:
            if not self.custom_validator(value):
                raise ValidationError(
                    message=self.custom_error or f"{self.name} is invalid",
                    field=self.name,
                )

        return value


# Common field validators
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
USERNAME_PATTERN = r"^[a-zA-Z0-9_.-]{3,30}$"


def email_field(name: str = "email", required: bool = True) -> FieldValidator:
    """Create an email field validator."""
    return FieldValidator(
        name=name,
        field_type=str,
        required=required,
        max_length=254,
        pattern=EMAIL_PATTERN,
        lowercase=True,
        custom_error="Please enter a valid email address",
    )


def username_field(name: str = "username", required: bool = True) -> FieldValidator:
    """Create a username field validator."""
    return FieldValidator(
        name=name,
        field_type=str,
        required=required,
        min_length=3,
        max_length=30,
        pattern=USERNAME_PATTERN,
        custom_error="Username must be 3-30 characters and contain only letters, numbers, underscores, dots, or hyphens",
    )


def password_field(name: str = "password", required: bool = True) -> FieldValidator:
    """Create a password field validator."""
    return FieldValidator(
        name=name,
        field_type=str,
        required=required,
        min_length=8,
        max_length=128,
        strip_whitespace=False,  # Preserve whitespace in passwords
    )


def text_field(
    name: str,
    required: bool = True,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> FieldValidator:
    """Create a text field validator."""
    return FieldValidator(
        name=name,
        field_type=str,
        required=required,
        min_length=min_length,
        max_length=max_length,
    )


def integer_field(
    name: str,
    required: bool = True,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> FieldValidator:
    """Create an integer field validator."""
    return FieldValidator(
        name=name,
        field_type=int,
        required=required,
        min_value=min_value,
        max_value=max_value,
    )


def boolean_field(name: str, required: bool = False, default: bool = False) -> FieldValidator:
    """Create a boolean field validator."""
    return FieldValidator(
        name=name,
        field_type=bool,
        required=required,
        default=default,
    )


def enum_field(name: str, allowed_values: Set[Any], required: bool = True) -> FieldValidator:
    """Create an enum field validator."""
    return FieldValidator(
        name=name,
        field_type=str,
        required=required,
        allowed_values=allowed_values,
    )


@dataclass
class ValidationSchema:
    """Schema for validating request data."""

    fields: List[FieldValidator] = field(default_factory=list)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against the schema.

        Args:
            data: Dictionary of data to validate

        Returns:
            Dictionary of validated and transformed data

        Raises:
            ValidationError: If any field fails validation
        """
        if not isinstance(data, dict):
            raise ValidationError(message="Request body must be a JSON object")

        validated = {}
        errors = []

        for field_validator in self.fields:
            try:
                value = data.get(field_validator.name)
                validated[field_validator.name] = field_validator.validate(value)
            except ValidationError as e:
                errors.append({
                    "field": field_validator.name,
                    "message": e.message,
                })

        if errors:
            raise ValidationError(
                message="Validation failed",
                details={"errors": errors},
            )

        return validated

    def add_field(self, validator: FieldValidator) -> "ValidationSchema":
        """Add a field validator to the schema."""
        self.fields.append(validator)
        return self


def validate_request(schema: ValidationSchema):
    """
    Decorator for validating request JSON body against a schema.

    Usage:
        @validate_request(my_schema)
        def my_endpoint(validated_data):
            # validated_data contains the validated request data
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            validated_data = schema.validate(data)
            return func(*args, validated_data=validated_data, **kwargs)

        return wrapper

    return decorator


# Pre-built schemas for common operations

LOGIN_SCHEMA = ValidationSchema(
    fields=[
        FieldValidator(
            name="identifier",
            field_type=str,
            required=True,
            min_length=1,
            max_length=254,
        ),
        password_field(),
    ]
)

REGISTER_SCHEMA = ValidationSchema(
    fields=[
        text_field("first_name", max_length=50),
        text_field("last_name", max_length=50),
        username_field(),
        email_field(),
        password_field(),
    ]
)

UPDATE_PREFERENCES_SCHEMA = ValidationSchema(
    fields=[
        enum_field("preferred_language", {"en", "es", "pt"}, required=False),
        enum_field("preferred_theme", {"light", "dark"}, required=False),
    ]
)

CREATE_JOURNAL_SCHEMA = ValidationSchema(
    fields=[
        text_field("title", min_length=1, max_length=200),
        text_field("source_text", required=False, max_length=10000),
        FieldValidator(name="analysis_json", field_type=dict, required=False),
        text_field("journal_text", required=False, max_length=50000),
    ]
)

UPDATE_JOURNAL_SCHEMA = ValidationSchema(
    fields=[
        text_field("title", required=False, max_length=200),
        text_field("journal_text", required=False, max_length=50000),
    ]
)

ANALYZE_TEXT_SCHEMA = ValidationSchema(
    fields=[
        text_field("text", min_length=1, max_length=5000),
        enum_field("locale", {"en", "es", "pt"}, required=False),
        text_field("region", required=False, max_length=10),
        text_field("token", required=False, max_length=100),
    ]
)

FEEDBACK_SCHEMA = ValidationSchema(
    fields=[
        text_field("entry_text", min_length=1, max_length=5000),
        FieldValidator(name="analysis_json", field_type=dict, required=False),
        text_field("feedback_text", min_length=1, max_length=2000),
    ]
)

PASSWORD_RESET_SCHEMA = ValidationSchema(
    fields=[
        email_field(),
        text_field("first_name", max_length=50),
        text_field("last_name", max_length=50),
        password_field("new_password"),
        password_field("confirm_password"),
    ]
)
