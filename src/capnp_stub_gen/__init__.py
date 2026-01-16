"""Cap'n Proto stub generator for Python.

Generate Python type stubs (.pyi files) from Cap'n Proto schema files.
"""

from __future__ import annotations

from capnp_stub_gen.generator import StubGenerator
from capnp_stub_gen.types import CAPNP_TYPE_TO_PYTHON, CapnpElementType, CapnpFieldType

__version__ = "0.1.0"
__all__ = [
    "CAPNP_TYPE_TO_PYTHON",
    "CapnpElementType",
    "CapnpFieldType",
    "StubGenerator",
]
