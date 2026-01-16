"""Tests for the types module."""

from __future__ import annotations

from capnp_stub_gen.types import CAPNP_TYPE_TO_PYTHON, CapnpElementType, CapnpFieldType


class TestCapnpTypeToPython:
    """Tests for the CAPNP_TYPE_TO_PYTHON mapping."""

    def test_void_maps_to_none(self) -> None:
        """Void type should map to None."""
        assert CAPNP_TYPE_TO_PYTHON["void"] == "None"

    def test_bool_maps_to_bool(self) -> None:
        """Bool type should map to bool."""
        assert CAPNP_TYPE_TO_PYTHON["bool"] == "bool"

    def test_integer_types_map_to_int(self) -> None:
        """All integer types should map to int."""
        int_types = ["int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"]
        for int_type in int_types:
            assert CAPNP_TYPE_TO_PYTHON[int_type] == "int"

    def test_float_types_map_to_float(self) -> None:
        """Float types should map to float."""
        assert CAPNP_TYPE_TO_PYTHON["float32"] == "float"
        assert CAPNP_TYPE_TO_PYTHON["float64"] == "float"

    def test_text_maps_to_str(self) -> None:
        """Text type should map to str."""
        assert CAPNP_TYPE_TO_PYTHON["text"] == "str"

    def test_data_maps_to_bytes(self) -> None:
        """Data type should map to bytes."""
        assert CAPNP_TYPE_TO_PYTHON["data"] == "bytes"

    def test_all_primitive_types_covered(self) -> None:
        """All primitive Cap'n Proto types should be in the mapping."""
        expected_types = {
            "void",
            "bool",
            "int8",
            "int16",
            "int32",
            "int64",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "float32",
            "float64",
            "text",
            "data",
        }
        assert set(CAPNP_TYPE_TO_PYTHON.keys()) == expected_types


class TestCapnpFieldType:
    """Tests for the CapnpFieldType enum."""

    def test_group_value(self) -> None:
        """GROUP should have value 'group'."""
        assert CapnpFieldType.GROUP == "group"
        assert CapnpFieldType.GROUP.value == "group"

    def test_slot_value(self) -> None:
        """SLOT should have value 'slot'."""
        assert CapnpFieldType.SLOT == "slot"
        assert CapnpFieldType.SLOT.value == "slot"

    def test_is_str_enum(self) -> None:
        """CapnpFieldType should be a string enum."""
        assert isinstance(CapnpFieldType.GROUP, str)
        assert isinstance(CapnpFieldType.SLOT, str)


class TestCapnpElementType:
    """Tests for the CapnpElementType enum."""

    def test_all_element_types_present(self) -> None:
        """All expected element types should be present."""
        expected = {"bool", "enum", "struct", "const", "void", "list", "anyPointer", "interface"}
        actual = {e.value for e in CapnpElementType}
        assert actual == expected

    def test_is_str_enum(self) -> None:
        """CapnpElementType should be a string enum."""
        for element_type in CapnpElementType:
            assert isinstance(element_type, str)

    def test_enum_value(self) -> None:
        """ENUM should have value 'enum'."""
        assert CapnpElementType.ENUM == "enum"

    def test_struct_value(self) -> None:
        """STRUCT should have value 'struct'."""
        assert CapnpElementType.STRUCT == "struct"

    def test_list_value(self) -> None:
        """LIST should have value 'list'."""
        assert CapnpElementType.LIST == "list"

    def test_any_pointer_value(self) -> None:
        """ANY_POINTER should have value 'anyPointer'."""
        assert CapnpElementType.ANY_POINTER == "anyPointer"
