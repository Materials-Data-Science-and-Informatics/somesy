"""Core somesy functions."""

import json
import logging
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

import tomlkit

from .log import VERBOSE

logger = logging.getLogger("somesy")

INPUT_FILES_ORDERED = [
    ".somesy.toml",
    "somesy.toml",
    "pyproject.toml",
    "package.json",
    "Project.toml",
    "fpm.toml",
    "Cargo.toml",
]
"""Input files ordered by priority for discovery."""


def atomic_write(
    path: Path,
    data: str | bytes,
    *,
    newline: str | None = None,
    exclusive: bool = False,
) -> None:
    """Write a file atomically: a failure never leaves a truncated or partial file.

    The data is written to a temporary file in the same directory, which then
    replaces the target. The mode of an existing target is kept; text is
    encoded as UTF-8.

    Args:
        path: Target file.
        data: Text or bytes to write; serialize before calling.
        newline: Newline translation for text, as for `open`.
        exclusive: Raise `FileExistsError` instead of replacing an existing file.

    """
    path = Path(path)
    if exclusive and path.exists():
        raise FileExistsError(f"File already exists: {path}")
    if path.is_symlink():
        path = path.resolve()
    if path.exists():
        mode = stat.S_IMODE(path.stat().st_mode)
    else:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created missing folder '{path.parent}'.")
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        if isinstance(data, bytes):
            with os.fdopen(fd, "wb") as binary:
                binary.write(data)
        else:
            with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as text:
                text.write(data)
        os.chmod(tmp_name, mode)
        try:
            os.replace(tmp_name, path)
        except PermissionError as err:
            # e.g. on Windows when another program has the target open
            if not path.exists():
                raise
            try:
                if isinstance(data, bytes):
                    with open(path, "wb") as binary:
                        binary.write(data)
                else:
                    with open(path, "w", encoding="utf-8", newline=newline) as text:
                        text.write(data)
            except OSError:
                raise err from None
            logger.warning(
                f"File '{path}' could not be replaced, wrote it directly instead."
            )
            Path(tmp_name).unlink(missing_ok=True)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def write_json(data: Any, path: Path) -> None:
    """Write data as UTF-8 JSON with 2-space indentation, unescaped non-ASCII and a trailing newline."""
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    atomic_write(path, text, newline="\n")


def discover_input(input_file: Path | None = None) -> Path:
    """Check given input file path. If not given, find somesy configuration file path from default list.

    Args:
        input_file: somesy configuration file path. Defaults to None.

    Raises:
        FileNotFoundError: Raised if no somesy input file found from cli input or the defaults.

    Returns:
        somesy configuration file path.

    """
    missing: Path | None = None
    if input_file:
        if input_file.is_file():
            logger.info(f"Using provided file '{input_file}' as somesy input file.")
            return input_file
        else:
            missing = input_file
            logger.warning(
                f"Passed file '{input_file}' does not exist. Searching for usable somesy input file..."
            )

    for filename in INPUT_FILES_ORDERED:
        input_file = Path(filename)
        if input_file.is_file():
            try:
                get_input_content(input_file)
            except RuntimeError:
                continue
            except (ValueError, TypeError, KeyError, OSError) as e:
                # NOTE: tomlkit and json parse errors are ValueError subclasses
                logger.warning(f"Skipping malformed input file '{input_file}': {e}")
                continue

            if missing is not None:
                logger.warning(
                    f"Input file '{missing}' does not exist, using '{input_file}' instead."
                )
            msg = f"Using '{input_file}' as somesy input file."
            logger.log(VERBOSE, msg)
            return input_file

    raise FileNotFoundError("No somesy input file found.")


def get_input_content(path: Path, *, no_unwrap: bool = False) -> dict[str, Any]:
    """Read contents of a supported somesy input file.

    Given a path to a TOML file, this function reads the file and returns its content as a TOMLDocument object.
    The function checks if the file is a valid somesy input file by checking its name and content.

    Args:
        path (Path): path to the input file
        no_unwrap (bool): if True, the function returns the TOMLDocument object instead of unwrapping it

    Returns:
        the content of the input file as a TOMLDocument object

    Raises:
        ValueError: if the input file is not a valid somesy input file or if the file is not a TOML file.
        RuntimeError: if the input file does not contain a somesy input section at expected key

    """
    logger.debug(f"Path {path}")
    # somesy.toml / .somesy.toml
    if path.suffix == ".toml" and "somesy" in path.name:
        with open(path, "r", encoding="utf-8") as f:
            ret = tomlkit.load(f)
            return ret if no_unwrap else ret.unwrap()

    # pyproject.toml or fpm.toml
    if (path.suffix == ".toml" and "pyproject" in path.name) or path.name in [
        "Project.toml",
        "fpm.toml",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            input_content = tomlkit.load(f)
            if "tool" in input_content and "somesy" in input_content["tool"]:
                return input_content["tool"]["somesy"].unwrap()
            else:
                raise RuntimeError(
                    "No tool.somesy section found in pyproject.toml file!"
                )

    # Cargo.toml
    if path.name == "Cargo.toml":
        with open(path, "r", encoding="utf-8") as f:
            input_content = tomlkit.load(f)
            if (
                "package" in input_content
                and "metadata" in input_content["package"]
                and "somesy" in input_content["package"]["metadata"]
            ):
                return input_content["package"]["metadata"]["somesy"].unwrap()
            else:
                raise RuntimeError(
                    "No package.somesy section found in Cargo.toml file!"
                )

    # package.json
    if path.suffix == ".json" and "package" in path.name:
        with open(path, "r", encoding="utf-8") as f:
            input_content = json.load(f)
            if "somesy" in input_content:
                return input_content["somesy"]
            else:
                raise RuntimeError("No somesy section found in package.json file!")

    # no match:
    raise ValueError("Unsupported input file.")
