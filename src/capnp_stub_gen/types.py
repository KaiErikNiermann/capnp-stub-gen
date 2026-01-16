"""Type definitions and mappings for Cap'n Proto schemas.

This module provides the core type mappings between Cap'n Proto types
and their Python equivalents, as well as enums for field and element types.
"""

from __future__ import annotations

from enum import StrEnum
from types import ModuleType

# Type alias for the module registry
type ModuleRegistryType = dict[int, tuple[str, ModuleType]]


# Mapping from Cap'n Proto type names to Python type strings
CAPNP_TYPE_TO_PYTHON: dict[str, str] = {
    "void": "None",
    "bool": "bool",
    "int8": "int",
    "int16": "int",
    "int32": "int",
    "int64": "int",
    "uint8": "int",
    "uint16": "int",
    "uint32": "int",
    "uint64": "int",
    "float32": "float",
    "float64": "float",
    "text": "str",
    "data": "bytes",
}


class CapnpFieldType(StrEnum):
    """Types of Cap'n Proto fields."""

    GROUP = "group"
    SLOT = "slot"


class CapnpElementType(StrEnum):
    """Types of Cap'n Proto elements."""

    BOOL = "bool"
    ENUM = "enum"
    STRUCT = "struct"
    CONST = "const"
    VOID = "void"
    LIST = "list"
    ANY_POINTER = "anyPointer"
    INTERFACE = "interface"
