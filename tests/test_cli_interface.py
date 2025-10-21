"""Regression tests for the ``compute_god.cli`` module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
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


def test_search_command_lists_matches(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["search", "god"])
    captured = capsys.readouterr()
    assert exit_code == 0
    lines = captured.out.strip().splitlines()
    assert lines[0] == "Search results for 'god':"
    assert any(line.endswith("core.God") for line in lines)


def test_search_command_supports_json_output(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["search", "core", "--format", "json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["query"] == "core"
    assert payload["matches"]
    assert any(item["reference"] == "core.God" for item in payload["matches"])


def test_search_command_respects_case_sensitivity(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["search", "god", "--case-sensitive"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "no matches" in captured.out


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


def test_wormhole_lab_cli_generates_json(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    np = pytest.importorskip("numpy")

    config = {
        "legs": [
            {"label": "L0", "boundary": "left"},
            {"label": "R0", "boundary": "right"},
        ],
        "propagators": [
            {"source": "L0", "target": "R0", "amplitude": 1.0, "proper_time": 0.5},
        ],
        "temperature": 0.25,
    }

    config_path = tmp_path / "wormhole.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    exit_code = main(["wormhole-lab", str(config_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["left_labels"] == ["L0"]
    assert payload["right_labels"] == ["R0"]
    assert payload["temperature"] == pytest.approx(0.25)
    assert payload["propagator_matrix"] == [[pytest.approx(float(np.exp(-0.5 * 0.25)))]]

