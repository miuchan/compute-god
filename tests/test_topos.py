import math

from compute_god.topos import build_topos_map, format_topos_text


def test_build_topos_map_has_station_and_entry_nodes():
    topos_map = build_topos_map()

    station_nodes = [node for node in topos_map.nodes if node.kind == "station"]
    entry_nodes = [node for node in topos_map.nodes if node.kind == "entry"]

    assert station_nodes, "at least one station should be projected"
    assert entry_nodes, "entries should be projected for every station"
    assert len(topos_map.edges) == len(entry_nodes)

    station_ids = {node.identifier for node in station_nodes}
    for edge in topos_map.edges:
        assert edge.parent in station_ids

    for node in topos_map.nodes:
        x, y = node.coordinate
        assert math.isfinite(x)
        assert math.isfinite(y)


def test_format_topos_text_includes_projection_banner_and_entries():
    topos_map = build_topos_map()
    rendered = format_topos_text(topos_map)

    assert rendered.startswith("Topos projection of the guidance desk:")
    sample_entry = next(node.label for node in topos_map.nodes if node.kind == "entry")
    assert sample_entry in rendered
