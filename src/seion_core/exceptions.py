"""Domain-specific exceptions."""


class SeionError(Exception):
    """Base class for mathematically meaningful input or execution errors."""


class ShapeError(SeionError, ValueError):
    """Raised when a tensor or vector has an incompatible shape."""


class FieldError(SeionError, TypeError):
    """Raised when a value cannot be represented in the declared field."""


class ConventionError(SeionError, ValueError):
    """Raised when an operation mixes incompatible mathematical conventions."""

