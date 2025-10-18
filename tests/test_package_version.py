from __future__ import annotations

import tomllib

from pathlib import Path

from compute_god import __version__


def _pyproject_version() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as stream:
        data = tomllib.load(stream)
    return data["project"]["version"]


def test_package_version_matches_pyproject() -> None:
    assert __version__ == _pyproject_version()
