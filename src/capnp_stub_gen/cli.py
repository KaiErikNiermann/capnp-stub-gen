"""Command-line interface for capnp-stub-gen.

This module provides the Typer-based CLI for generating Python type stubs
from Cap'n Proto schema files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from capnp_stub_gen import __version__
from capnp_stub_gen.generator import StubGenerator


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"capnp-stub-gen {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="capnp-stub-gen",
    help="Generate Python type stubs from Cap'n Proto schema files.",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def main_callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Print version and exit.",
        ),
    ] = None,
) -> None:
    """Cap'n Proto stub generator for Python."""


@app.command()
def generate(
    schema: Annotated[
        Path,
        typer.Argument(
            help="Path to the .capnp schema file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "-o",
            "--output",
            help="Output directory for generated stubs.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    proto_path: Annotated[
        str | None,
        typer.Option(
            "--proto-path",
            help=(
                "Python expression for schema path in generated runtime module. "
                "Example: 'str(Path(__file__).parent / \"schema.capnp\")'"
            ),
        ),
    ] = None,
    no_runtime: Annotated[
        bool,
        typer.Option(
            "--no-runtime",
            help="Skip generating the runtime .py module.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Enable verbose output.",
        ),
    ] = False,
) -> None:
    """Generate Python type stubs from a Cap'n Proto schema file.

    This command generates .pyi stub files that provide type information
    for Pylance/Pyright when working with pycapnp schemas.
    """
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    try:
        generator = StubGenerator(schema)
        generated_files = generator.write_files(
            output_dir=output,
            proto_import_path=proto_path,
            generate_runtime=not no_runtime,
        )

        for path in generated_files:
            typer.echo(f"Generated: {path}")

    except FileNotFoundError as e:
        typer.echo(f"Error: File not found - {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(code=1) from e


@app.command()
def batch(
    schemas: Annotated[
        list[Path],
        typer.Argument(
            help="Paths to .capnp schema files.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "-o",
            "--output",
            help="Output directory for generated stubs.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    no_runtime: Annotated[
        bool,
        typer.Option(
            "--no-runtime",
            help="Skip generating the runtime .py modules.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Enable verbose output.",
        ),
    ] = False,
) -> None:
    """Generate Python type stubs from multiple Cap'n Proto schema files.

    This command processes multiple .capnp files in a single run.
    """
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    total_files: list[Path] = []
    errors: list[tuple[Path, str]] = []

    for schema_path in schemas:
        try:
            generator = StubGenerator(schema_path)
            generated_files = generator.write_files(
                output_dir=output,
                generate_runtime=not no_runtime,
            )
            total_files.extend(generated_files)

            for path in generated_files:
                typer.echo(f"Generated: {path}")

        except Exception as e:
            errors.append((schema_path, str(e)))
            typer.echo(f"Error processing {schema_path}: {e}", err=True)

    # Summary
    typer.echo()
    typer.echo(f"Generated {len(total_files)} files from {len(schemas)} schemas.")

    if errors:
        typer.echo(f"Encountered {len(errors)} errors.", err=True)
        raise typer.Exit(code=1)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
