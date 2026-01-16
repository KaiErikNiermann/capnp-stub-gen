"""Tests for the CLI module."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from capnp_stub_gen import __version__
from capnp_stub_gen.cli import app

runner = CliRunner()


class TestCLIVersion:
    """Tests for CLI version display."""

    def test_version_flag(self) -> None:
        """--version should display version and exit."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_short_flag(self) -> None:
        """-V should display version and exit."""
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestCLIGenerate:
    """Tests for the generate command."""

    def test_generate_requires_schema(self) -> None:
        """Generate command should require a schema argument."""
        result = runner.invoke(app, ["generate"])
        assert result.exit_code != 0

    def test_generate_nonexistent_file(self, temp_dir: Path) -> None:
        """Generate should fail for nonexistent schema file."""
        result = runner.invoke(app, ["generate", str(temp_dir / "nonexistent.capnp")])
        assert result.exit_code != 0

    def test_generate_simple_schema(self, simple_schema_path: Path, temp_dir: Path) -> None:
        """Generate should create stub files for valid schema."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["generate", str(simple_schema_path), "-o", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Generated:" in result.stdout
        assert (output_dir / "simple.pyi").exists()
        assert (output_dir / "simple.py").exists()

    def test_generate_no_runtime(self, simple_schema_path: Path, temp_dir: Path) -> None:
        """Generate with --no-runtime should skip .py file."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["generate", str(simple_schema_path), "-o", str(output_dir), "--no-runtime"],
        )

        assert result.exit_code == 0
        assert (output_dir / "simple.pyi").exists()
        assert not (output_dir / "simple.py").exists()

    def test_generate_verbose(self, simple_schema_path: Path, temp_dir: Path) -> None:
        """Generate with --verbose should enable verbose output."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["generate", str(simple_schema_path), "-o", str(output_dir), "-v"],
        )

        assert result.exit_code == 0

    def test_generate_with_proto_path(self, simple_schema_path: Path, temp_dir: Path) -> None:
        """Generate with --proto-path should use custom path in runtime module."""
        output_dir = temp_dir / "output"
        custom_path = 'str(Path(__file__).parent / "schema.capnp")'

        result = runner.invoke(
            app,
            [
                "generate",
                str(simple_schema_path),
                "-o",
                str(output_dir),
                "--proto-path",
                custom_path,
            ],
        )

        assert result.exit_code == 0

        # Check the generated runtime module contains the custom path
        runtime_content = (output_dir / "simple.py").read_text()
        assert custom_path in runtime_content


class TestCLIBatch:
    """Tests for the batch command."""

    def test_batch_multiple_schemas(
        self,
        simple_schema_path: Path,
        enum_schema_path: Path,
        temp_dir: Path,
    ) -> None:
        """Batch command should process multiple schemas."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            [
                "batch",
                str(simple_schema_path),
                str(enum_schema_path),
                "-o",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert (output_dir / "simple.pyi").exists()
        assert (output_dir / "enums.pyi").exists()
        assert "Generated 4 files from 2 schemas" in result.stdout

    def test_batch_no_runtime(
        self,
        simple_schema_path: Path,
        enum_schema_path: Path,
        temp_dir: Path,
    ) -> None:
        """Batch with --no-runtime should skip .py files."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            [
                "batch",
                str(simple_schema_path),
                str(enum_schema_path),
                "-o",
                str(output_dir),
                "--no-runtime",
            ],
        )

        assert result.exit_code == 0
        assert (output_dir / "simple.pyi").exists()
        assert (output_dir / "enums.pyi").exists()
        assert not (output_dir / "simple.py").exists()
        assert not (output_dir / "enums.py").exists()
        assert "Generated 2 files from 2 schemas" in result.stdout


class TestCLINoArgsHelp:
    """Tests for CLI help display."""

    def test_no_args_shows_help(self) -> None:
        """Running without arguments should show help."""
        result = runner.invoke(app, [])
        # Typer shows help when no_args_is_help=True (exit code 0 with typer)
        # The help text contains usage info
        assert "Usage:" in result.stdout or "generate" in result.stdout
