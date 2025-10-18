"""Regression tests for the ``compute_god.cli`` module."""

from __future__ import annotations

import json

from pytest import CaptureFixture

from compute_god.cli import main


def _read_version() -> str:
    from compute_god import __version__

    return __version__


def test_stations_text_output(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["stations"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "core" in captured.out
    assert "- God" in captured.out


def test_stations_json_output(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["stations", "--format", "json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert "core" in payload
    assert "entries" in payload["core"]


def test_station_lookup(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["station", "core"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.splitlines()[0] == "core"
    assert "God" in captured.out


def test_resolve_reference(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["resolve", "core.God"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "compute_god.core.universe.God" in captured.out


def test_unknown_station_returns_error(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["station", "does-not-exist"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unknown station" in captured.err


def test_unknown_reference_returns_error(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["resolve", "core.unknown"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unknown guidance reference" in captured.err


def test_version_command_outputs_package_version(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == _read_version()

