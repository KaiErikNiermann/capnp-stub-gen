# capnp-stub-gen

Generate Python type stubs (.pyi files) from Cap'n Proto schema files.

This tool parses `.capnp` files using pycapnp and generates `.pyi` stub files
that provide proper type information for Pylance/Pyright.

## Features

- Generates type stubs for Cap'n Proto structs (Reader and Builder classes)
- Supports enums with proper type definitions
- Handles nested structs and lists
- Generates runtime Python modules for easy schema loading
- CLI interface with batch processing support
- Full type annotations for strict type checking

## Requirements

- Python 3.14+
- pycapnp 2.0+
- Cap'n Proto compiler (capnp) installed on your system

## Installation

```bash
pip install capnp-stub-gen
```

Or using Poetry:

```bash
poetry add capnp-stub-gen
```

## Usage

### Command Line

Generate stubs for a single schema:

```bash
capnp-stub-gen generate path/to/schema.capnp -o output/
```

Generate stubs for multiple schemas:

```bash
capnp-stub-gen batch schema1.capnp schema2.capnp -o output/
```

### Options

```
capnp-stub-gen generate [OPTIONS] SCHEMA

Arguments:
  SCHEMA                    Path to the .capnp schema file

Options:
  -o, --output PATH         Output directory for generated stubs [default: .]
  --proto-path TEXT         Python expression for schema path in runtime module
  --no-runtime              Skip generating the runtime .py module
  -v, --verbose             Enable verbose output
  --version                 Print version and exit
  --help                    Show this message and exit
```

### Python API

```python
from pathlib import Path
from capnp_stub_gen import StubGenerator

# Generate stubs
generator = StubGenerator("path/to/schema.capnp")
generator.write_files(Path("output/"))

# Or get the stub content as a string
stub_content = generator.generate_stub()
print(stub_content)
```

## Generated Files

For a schema file `myschema.capnp`, the tool generates:

- `myschema.pyi` - Type stub file with all type definitions
- `myschema.py` - Runtime module that loads and exports the schema

### Example

Given a schema:

```capnp
@0xabcdef1234567890;

struct Person {
  name @0 :Text;
  age @1 :UInt32;
  email @2 :Text;
}
```

The generated stub includes:

```python
class PersonReader:
    """Reader for Person Cap'n Proto struct."""

    @property
    def name(self) -> str: ...

    @property
    def age(self) -> int: ...

    @property
    def email(self) -> str: ...

class PersonBuilder:
    """Builder for Person Cap'n Proto struct."""

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, value: str) -> None: ...

    # ... etc
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/capnp-stub-gen.git
cd capnp-stub-gen

# Install dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run type checking
poetry run pyright src/

# Run linting
poetry run ruff check src/ tests/
```

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=capnp_stub_gen --cov-report=html

# Specific test file
poetry run pytest tests/test_generator.py
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.
