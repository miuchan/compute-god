from compute_god.intelligent_driving_lab import (
    build_intelligent_driving_lab,
    find_capabilities_with_sensor,
    iter_module_highlights,
    lab_summary_table,
    scenarios_covering_capability,
)


def test_lab_basic_structure():
    lab = build_intelligent_driving_lab()

    assert lab.hero_title == "Intelligent Driving Lab"
    assert "Perception" in lab.tagline
    assert len(lab.capabilities) >= 5
    assert len(lab.sections) == 3


def test_find_capabilities_with_sensor_matches_lidar():
    lab = build_intelligent_driving_lab()

    lidar_caps = find_capabilities_with_sensor(lab, "lidar")

    assert {cap.name for cap in lidar_caps} == {"Perception Fusion"}


def test_scenarios_covering_capability_are_consistent():
    lab = build_intelligent_driving_lab()

    planning_scenarios = scenarios_covering_capability(lab, "Planning & Control")
    assert {scenario.slug for scenario in planning_scenarios} == {
        "beijing-night-market",
        "chengdu-ring-road",
    }


def test_lab_summary_table_formats_rows():
    lab = build_intelligent_driving_lab()

    table = lab_summary_table(lab)

    assert len(table) == len(lab.scenarios)
    first_row = table[0]
    assert set(first_row.keys()) == {"Scenario", "Environment", "Focus", "Evaluation"}
    assert "Beijing" in first_row["Scenario"]


def test_iter_module_highlights_is_exhaustive():
    lab = build_intelligent_driving_lab()

    highlights = list(iter_module_highlights(lab))
    expected_count = sum(len(section.modules) for section in lab.sections)

    assert len(highlights) == expected_count
    assert any("widget" in highlight for highlight in highlights)

