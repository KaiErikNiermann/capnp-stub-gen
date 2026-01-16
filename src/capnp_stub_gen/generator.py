"""Stub generator for Cap'n Proto schema files.

This module provides the main StubGenerator class that parses Cap'n Proto
schema files and generates Python type stub files (.pyi).
"""

from __future__ import annotations

import logging
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

import capnp as _capnp  # type: ignore[import-untyped]

from capnp_stub_gen.types import CAPNP_TYPE_TO_PYTHON, CapnpElementType, CapnpFieldType

if TYPE_CHECKING:
    from types import ModuleType

logger = logging.getLogger(__name__)

# Discriminant value indicating a field is not part of a union
_NOT_IN_UNION = 65535


class StubGenerator:
    """Generate Python type stubs from Cap'n Proto schema files."""

    def __init__(self, schema_path: str | Path) -> None:
        """Initialize the stub generator with a schema path.

        Args:
            schema_path: Path to the .capnp schema file.
        """
        self.schema_path = Path(schema_path)
        self._schema: ModuleType | None = None
        self._type_registry: dict[int, str] = {}
        self._struct_names: list[str] = []
        self._enum_names: list[str] = []
        self._const_names: list[tuple[str, str, Any]] = []  # (name, py_type, value)
        self._struct_fields: dict[str, list[tuple[str, str, bool]]] = {}  # struct -> [(field, type, is_union)]
        self._struct_union_fields: dict[str, list[str]] = {}  # struct -> [union field names]

    @property
    def schema(self) -> ModuleType:
        """Load and return the schema module."""
        if self._schema is None:
            self._schema = _capnp.load(str(self.schema_path))  # type: ignore[no-untyped-call]
            self._collect_types()
        return self._schema  # type: ignore[return-value]

    def _collect_types(self) -> None:
        """Collect all types from the loaded schema."""
        if self._schema is None:
            return

        for name in dir(self._schema):
            if name.startswith("_"):
                continue

            obj = getattr(self._schema, name)
            obj_schema = getattr(obj, "schema", None)

            if obj_schema is None:
                continue

            node = getattr(obj_schema, "node", None)
            if node is not None:
                type_id = node.id
                self._type_registry[type_id] = name
                logger.debug("Registered type: %s (id=%d)", name, type_id)

                # Check for const
                node_which = node.which()
                if node_which == "const":
                    self._collect_const(name, node)
                    continue

            if hasattr(obj_schema, "fields"):
                self._struct_names.append(name)
                self._collect_struct_fields(name, obj_schema)
            elif hasattr(obj_schema, "enumerants"):
                self._enum_names.append(name)

    def _collect_const(self, name: str, node: Any) -> None:
        """Collect a const definition.

        Args:
            name: The const name.
            node: The schema node.
        """
        const_type = node.const.type.which()
        if const_type in CAPNP_TYPE_TO_PYTHON:
            py_type = CAPNP_TYPE_TO_PYTHON[const_type]
            self._const_names.append((name, py_type, None))
            logger.debug("Registered const: %s -> %s", name, py_type)

    def _collect_struct_fields(self, struct_name: str, schema: Any) -> None:
        """Collect field information for a struct including union membership.

        Args:
            struct_name: Name of the struct.
            schema: The schema object.
        """
        union_fields: list[str] = []
        fields: list[tuple[str, str, bool]] = []

        for field_name, field_obj in schema.fields.items():
            proto = field_obj.proto
            is_union = proto.discriminantValue != _NOT_IN_UNION

            if is_union:
                union_fields.append(field_name)

            py_type = self._get_field_type(field_obj)
            fields.append((field_name, py_type, is_union))

        self._struct_fields[struct_name] = fields
        self._struct_union_fields[struct_name] = union_fields

    def _get_field_type(self, field_obj: Any) -> str:
        """Get the Python type annotation for a Cap'n Proto field.

        Args:
            field_obj: The pycapnp field object.

        Returns:
            The Python type annotation string.
        """
        proto = field_obj.proto

        match proto.which():
            case CapnpFieldType.GROUP:
                type_id = proto.group.typeId
                return self._type_registry.get(type_id, "Any")

            case CapnpFieldType.SLOT:
                return self._get_slot_type(proto.slot.type)

            case _:
                return "Any"

    def _get_slot_type(self, slot_type: Any) -> str:
        """Get the Python type for a slot type.

        Args:
            slot_type: The pycapnp slot type object.

        Returns:
            The Python type annotation string.
        """
        type_which = slot_type.which()

        if type_which in CAPNP_TYPE_TO_PYTHON:
            return CAPNP_TYPE_TO_PYTHON[type_which]

        match type_which:
            case CapnpElementType.STRUCT:
                type_id = slot_type.struct.typeId
                return self._type_registry.get(type_id, "Any")

            case CapnpElementType.ENUM:
                type_id = slot_type.enum.typeId
                return self._type_registry.get(type_id, "int")

            case CapnpElementType.LIST:
                return self._get_list_type(slot_type.list.elementType)

            case CapnpElementType.ANY_POINTER:
                return "Any"

            case _:
                return "Any"

    def _get_list_type(self, element_type: Any) -> str:
        """Get the Python type for a list element type.

        Args:
            element_type: The pycapnp element type object.

        Returns:
            The Python list type annotation string.
        """
        elem_which = element_type.which()

        if elem_which in CAPNP_TYPE_TO_PYTHON:
            return f"list[{CAPNP_TYPE_TO_PYTHON[elem_which]}]"

        match elem_which:
            case CapnpElementType.STRUCT:
                type_id = element_type.struct.typeId
                inner_type = self._type_registry.get(type_id, "Any")
                return f"list[{inner_type}]"

            case CapnpElementType.ENUM:
                type_id = element_type.enum.typeId
                inner_type = self._type_registry.get(type_id, "int")
                return f"list[{inner_type}]"

            case CapnpElementType.LIST:
                inner_type = self._get_list_type(element_type.list.elementType)
                return f"list[{inner_type}]"

            case _:
                return "list[Any]"

    def _write_header(self, out: TextIO, schema_name: str) -> None:
        """Write the stub file header."""
        out.write(f'"""Type stubs for {schema_name} Cap\'n Proto schema.\n\n')
        out.write("Auto-generated by capnp-stub-gen. Do not edit manually.\n")
        out.write('"""\n\n')
        out.write("from __future__ import annotations\n\n")
        out.write("from contextlib import contextmanager\n")
        out.write("from io import BufferedWriter\n")
        out.write("from typing import Any, Iterator, Literal, Self, overload\n\n")

    def _write_const(self, out: TextIO, name: str, py_type: str) -> None:
        """Write a const definition.

        Args:
            out: TextIO to write to.
            name: The const name.
            py_type: The Python type annotation.
        """
        out.write(f"{name}: {py_type}\n")

    def _write_enum(self, out: TextIO, name: str) -> None:
        """Write an enum class definition."""
        obj = getattr(self.schema, name)
        out.write(f"class {name}:\n")
        out.write(f'    """Cap\'n Proto enum: {name}."""\n\n')

        for enumerant_name in obj.schema.enumerants:
            out.write(f"    {enumerant_name}: int\n")

        out.write("\n")

    def _write_reader_class(self, out: TextIO, name: str) -> None:
        """Write a Reader class for a struct."""
        obj = getattr(self.schema, name)
        fields = obj.schema.fields

        out.write(f"class {name}Reader:\n")
        out.write(f'    """Reader for {name} Cap\'n Proto struct."""\n\n')

        for field_name, field_obj in fields.items():
            py_type = self._get_field_type(field_obj)

            # Append Reader suffix for struct types
            if py_type in self._struct_names:
                py_type = f"{py_type}Reader"
            elif py_type.startswith("list[") and py_type[5:-1] in self._struct_names:
                inner = py_type[5:-1]
                py_type = f"list[{inner}Reader]"

            out.write("    @property\n")
            out.write(f"    def {field_name}(self) -> {py_type}:\n")
            out.write("        ...\n\n")

        self._write_common_reader_methods(out, name)
        out.write("\n")

    def _write_common_reader_methods(self, out: TextIO, name: str) -> None:
        """Write common methods for Reader classes."""
        out.write("    def to_dict(self) -> dict[str, Any]:\n")
        out.write("        ...\n\n")
        out.write("    def to_bytes(self) -> bytes:\n")
        out.write("        ...\n\n")
        out.write("    def to_bytes_packed(self) -> bytes:\n")
        out.write("        ...\n\n")

        # Generate typed which() return if struct has union fields
        union_fields = self._struct_union_fields.get(name, [])
        if union_fields:
            literal_type = ", ".join(f'"{f}"' for f in union_fields)
            out.write(f"    def which(self) -> Literal[{literal_type}]:\n")
        else:
            out.write("    def which(self) -> str:\n")
        out.write("        ...\n")

    def _write_builder_class(self, out: TextIO, name: str) -> None:
        """Write a Builder class for a struct."""
        obj = getattr(self.schema, name)
        fields = obj.schema.fields

        out.write(f"class {name}Builder:\n")
        out.write(f'    """Builder for {name} Cap\'n Proto struct."""\n\n')

        for field_name, field_obj in fields.items():
            py_type = self._get_field_type(field_obj)

            if py_type in self._struct_names:
                builder_type = f"{py_type}Builder"
            elif py_type.startswith("list[") and py_type[5:-1] in self._struct_names:
                inner = py_type[5:-1]
                builder_type = f"list[{inner}Builder]"
            else:
                builder_type = py_type

            out.write("    @property\n")
            out.write(f"    def {field_name}(self) -> {builder_type}:\n")
            out.write("        ...\n\n")
            out.write(f"    @{field_name}.setter\n")
            out.write(f"    def {field_name}(self, value: {py_type}) -> None:\n")
            out.write("        ...\n\n")

        self._write_common_builder_methods(out, name)
        out.write("\n")

    def _write_common_builder_methods(self, out: TextIO, name: str) -> None:
        """Write common methods for Builder classes."""
        out.write("    def to_dict(self) -> dict[str, Any]:\n")
        out.write("        ...\n\n")
        out.write("    def to_bytes(self) -> bytes:\n")
        out.write("        ...\n\n")
        out.write("    def to_bytes_packed(self) -> bytes:\n")
        out.write("        ...\n\n")
        out.write("    def to_segments(self) -> list[bytes]:\n")
        out.write("        ...\n\n")
        out.write(f"    def as_reader(self) -> {name}Reader:\n")
        out.write("        ...\n\n")
        out.write("    def copy(self) -> Self:\n")
        out.write("        ...\n\n")
        out.write("    @staticmethod\n")
        out.write(f"    def from_dict(d: dict[str, Any]) -> {name}Builder:\n")
        out.write("        ...\n\n")

        # Generate typed overloaded init() methods for struct fields
        self._write_init_overloads(out, name)

        out.write("    def write(self, file: BufferedWriter) -> None:\n")
        out.write("        ...\n\n")
        out.write("    def write_packed(self, file: BufferedWriter) -> None:\n")
        out.write("        ...\n\n")

        # Generate typed which() return if struct has union fields
        union_fields = self._struct_union_fields.get(name, [])
        if union_fields:
            literal_type = ", ".join(f'"{f}"' for f in union_fields)
            out.write(f"    def which(self) -> Literal[{literal_type}]:\n")
        else:
            out.write("    def which(self) -> str:\n")
        out.write("        ...\n")

    def _write_init_overloads(self, out: TextIO, name: str) -> None:
        """Write overloaded init() methods for struct fields.

        Args:
            out: TextIO to write to.
            name: The struct name.
        """
        fields = self._struct_fields.get(name, [])

        # Filter to fields that are structs or lists (can be initialized)
        init_fields: list[tuple[str, str]] = []
        for field_name, py_type, _ in fields:
            # Check if this is a struct type (can init) or list type (can init with size)
            if py_type in self._struct_names:
                init_fields.append((field_name, f"{py_type}Builder"))
            elif py_type.startswith("list["):
                inner = py_type[5:-1]
                if inner in self._struct_names:
                    init_fields.append((field_name, f"list[{inner}Builder]"))
                else:
                    init_fields.append((field_name, py_type))

        if init_fields:
            # Write typed overloads for each field
            for field_name, return_type in init_fields:
                out.write("    @overload\n")
                out.write(f'    def init(self, name: Literal["{field_name}"]) -> {return_type}:\n')
                out.write("        ...\n\n")
                out.write("    @overload\n")
                out.write(f'    def init(self, name: Literal["{field_name}"], size: int) -> {return_type}:\n')
                out.write("        ...\n\n")

        # Always write the catch-all overload
        out.write("    @overload\n")
        out.write("    def init(self, name: str) -> Any:\n")
        out.write("        ...\n\n")
        out.write("    @overload\n")
        out.write("    def init(self, name: str, size: int) -> Any:\n")
        out.write("        ...\n\n")
        out.write("    def init(self, name: str, size: int | None = None) -> Any:\n")
        out.write("        ...\n\n")

    def _write_struct_module(self, out: TextIO, name: str) -> None:
        """Write a struct module class (the type you get from schema.TypeName)."""
        out.write(f"class _{name}Module:\n")
        out.write(f'    """Cap\'n Proto struct module: {name}."""\n\n')
        out.write("    schema: Any\n\n")
        out.write("    @staticmethod\n")
        out.write(f"    def new_message() -> {name}Builder:\n")
        out.write("        ...\n\n")
        out.write("    @staticmethod\n")
        out.write(f"    def read(msg: Any) -> {name}Reader:\n")
        out.write("        ...\n\n")
        out.write("    @staticmethod\n")
        out.write("    @contextmanager\n")
        out.write("    def from_bytes(\n")
        out.write("        data: bytes,\n")
        out.write("        traversal_limit_in_words: int | None = ...,\n")
        out.write("        nesting_limit: int | None = ...,\n")
        out.write(f"    ) -> Iterator[{name}Reader]:\n")
        out.write("        ...\n\n")
        out.write("    @staticmethod\n")
        out.write("    def from_bytes_packed(\n")
        out.write("        data: bytes,\n")
        out.write("        traversal_limit_in_words: int | None = ...,\n")
        out.write("        nesting_limit: int | None = ...,\n")
        out.write(f"    ) -> {name}Reader:\n")
        out.write("        ...\n\n")

    def _write_schema_module(self, out: TextIO, schema_name: str) -> None:
        """Write the main schema module class."""
        class_name = self._make_class_name(schema_name)

        out.write(f"class {class_name}:\n")
        out.write(f'    """Loaded {schema_name} Cap\'n Proto schema module."""\n\n')

        # Add const types first
        for name, py_type, _value in self._const_names:
            out.write(f"    {name}: {py_type}\n")

        for name in self._enum_names:
            out.write(f"    {name}: type[{name}]\n")

        for name in self._struct_names:
            out.write(f"    {name}: _{name}Module\n")

        out.write("\n\n")

        # Write the load function
        out.write(f"def load(path: str) -> {class_name}:\n")
        out.write('    """Load a Cap\'n Proto schema file."""\n')
        out.write("    ...\n\n\n")

        # Write module-level exports
        out.write("# Module-level exports (runtime values from loaded schema)\n")
        for name, py_type, _value in self._const_names:
            out.write(f"{name}: {py_type}\n")
        for name in self._enum_names:
            out.write(f"{name}: type[{name}]\n")
        for name in self._struct_names:
            out.write(f"{name}: _{name}Module\n")

    @staticmethod
    def _make_class_name(schema_name: str) -> str:
        """Convert a schema name to a PascalCase class name."""
        parts = schema_name.replace("-", "_").split("_")
        return "".join(part.capitalize() for part in parts) + "Schema"

    def generate_stub(self, out: TextIO | None = None) -> str:
        """Generate the stub file content.

        Args:
            out: Optional TextIO to write to. If None, returns the content as a string.

        Returns:
            The generated stub content as a string.
        """
        # Force schema loading
        _ = self.schema

        buffer = StringIO() if out is None else out
        schema_name = self.schema_path.stem

        self._write_header(buffer, schema_name)

        # Generate const definitions
        for name, py_type, _value in self._const_names:
            self._write_const(buffer, name, py_type)
        if self._const_names:
            buffer.write("\n")

        # Generate enum classes
        for name in self._enum_names:
            self._write_enum(buffer, name)

        # Generate Reader classes
        for name in self._struct_names:
            self._write_reader_class(buffer, name)

        # Generate Builder classes
        for name in self._struct_names:
            self._write_builder_class(buffer, name)

        # Generate struct module classes
        for name in self._struct_names:
            self._write_struct_module(buffer, name)

        # Generate schema module
        self._write_schema_module(buffer, schema_name)

        if isinstance(buffer, StringIO):
            return buffer.getvalue()
        return ""

    def generate_runtime_module(self, proto_import_path: str | None = None) -> str:
        """Generate a runtime Python module that loads and re-exports the schema.

        Args:
            proto_import_path: Optional Python expression for the schema path.

        Returns:
            The generated runtime module content as a string.
        """
        # Force schema loading
        _ = self.schema

        schema_name = self.schema_path.stem

        if proto_import_path is None:
            proto_import_path = f'"{self.schema_path.resolve()}"'

        buffer = StringIO()

        buffer.write(f'"""Runtime module for {schema_name} Cap\'n Proto schema.\n\n')
        buffer.write("This module loads the schema at import time and provides typed access.\n")
        buffer.write('"""\n\n')
        buffer.write("from __future__ import annotations\n\n")
        buffer.write("import capnp as _capnp\n\n")
        buffer.write(f"_SCHEMA_PATH = {proto_import_path}\n\n")
        buffer.write("# Load schema at module import\n")
        buffer.write("_schema = _capnp.load(_SCHEMA_PATH)\n\n")
        buffer.write("# Re-export all types\n")

        all_names: list[str] = []
        for const_name, _py_type, _value in self._const_names:
            buffer.write(f"{const_name} = _schema.{const_name}\n")
            all_names.append(const_name)

        for name in self._enum_names + self._struct_names:
            buffer.write(f"{name} = _schema.{name}\n")
            all_names.append(name)

        buffer.write("\n__all__ = [\n")
        for name in all_names:
            buffer.write(f'    "{name}",\n')
        buffer.write("]\n")

        return buffer.getvalue()

    def write_files(
        self,
        output_dir: Path,
        proto_import_path: str | None = None,
        generate_runtime: bool = True,
    ) -> list[Path]:
        """Write generated stub and runtime files to disk.

        Args:
            output_dir: Directory to write files to.
            proto_import_path: Optional Python expression for the schema path.
            generate_runtime: Whether to generate the runtime .py file.

        Returns:
            List of paths to generated files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files: list[Path] = []

        schema_name = self.schema_path.stem.replace("-", "_")

        # Write stub file
        stub_path = output_dir / f"{schema_name}.pyi"
        stub_content = self.generate_stub()
        stub_path.write_text(stub_content)
        generated_files.append(stub_path)
        logger.info("Generated stub file: %s", stub_path)

        # Write runtime module if requested
        if generate_runtime:
            py_path = output_dir / f"{schema_name}.py"
            runtime_content = self.generate_runtime_module(proto_import_path)
            py_path.write_text(runtime_content)
            generated_files.append(py_path)
            logger.info("Generated runtime module: %s", py_path)

        return generated_files
