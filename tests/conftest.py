"""Test fixtures and shared utilities for capnp-stub-gen tests."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# Simple Cap'n Proto schema for testing
# Generated IDs using capnp id
SIMPLE_SCHEMA = """\
@0xc47fae1087b46444;

struct Person {
  name @0 :Text;
  age @1 :UInt32;
  email @2 :Text;
}

struct Address {
  street @0 :Text;
  city @1 :Text;
  zipCode @2 :Text;
}
"""

# Schema with enums
ENUM_SCHEMA = """\
@0xa1ace8fbfe7fa406;

enum Color {
  red @0;
  green @1;
  blue @2;
}

enum Status {
  pending @0;
  active @1;
  completed @2;
  cancelled @3;
}

struct Item {
  name @0 :Text;
  color @1 :Color;
  status @2 :Status;
}
"""

# Schema with nested structs
NESTED_SCHEMA = """\
@0xfc8cec4e56038927;

struct Container {
  name @0 :Text;
  inner @1 :Inner;

  struct Inner {
    value @0 :Int32;
    description @1 :Text;
  }
}
"""

# Schema with lists
LIST_SCHEMA = """\
@0xc6036efc1ee5646d;

struct Collection {
  names @0 :List(Text);
  numbers @1 :List(Int32);
  flags @2 :List(Bool);
}
"""

# Complex schema with multiple features
COMPLEX_SCHEMA = """\
@0xb82368f30c573d4a;

enum Priority {
  low @0;
  medium @1;
  high @2;
  critical @3;
}

struct Task {
  id @0 :UInt64;
  title @1 :Text;
  description @2 :Text;
  priority @3 :Priority;
  completed @4 :Bool;
  tags @5 :List(Text);
  assignee @6 :User;
  subtasks @7 :List(Task);
}

struct User {
  id @0 :UInt64;
  name @1 :Text;
  email @2 :Text;
}

struct Project {
  name @0 :Text;
  tasks @1 :List(Task);
  owner @2 :User;
  members @3 :List(User);
}
"""


@pytest.fixture(scope="session")
def session_temp_dir() -> Generator[Path]:
    """Create a session-scoped temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def simple_schema_path(session_temp_dir: Path) -> Path:
    """Create a simple schema file for testing (session-scoped to avoid reloading issues)."""
    schema_path = session_temp_dir / "simple.capnp"
    schema_path.write_text(SIMPLE_SCHEMA)
    return schema_path


@pytest.fixture(scope="session")
def enum_schema_path(session_temp_dir: Path) -> Path:
    """Create a schema file with enums for testing (session-scoped)."""
    schema_path = session_temp_dir / "enums.capnp"
    schema_path.write_text(ENUM_SCHEMA)
    return schema_path


@pytest.fixture(scope="session")
def nested_schema_path(session_temp_dir: Path) -> Path:
    """Create a schema file with nested structs for testing (session-scoped)."""
    schema_path = session_temp_dir / "nested.capnp"
    schema_path.write_text(NESTED_SCHEMA)
    return schema_path


@pytest.fixture(scope="session")
def list_schema_path(session_temp_dir: Path) -> Path:
    """Create a schema file with lists for testing (session-scoped)."""
    schema_path = session_temp_dir / "lists.capnp"
    schema_path.write_text(LIST_SCHEMA)
    return schema_path


@pytest.fixture(scope="session")
def complex_schema_path(session_temp_dir: Path) -> Path:
    """Create a complex schema file for testing (session-scoped)."""
    schema_path = session_temp_dir / "complex.capnp"
    schema_path.write_text(COMPLEX_SCHEMA)
    return schema_path
