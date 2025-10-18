from compute_god.information_architecture import (
    encode_entry,
    recursive_gradient_descent_order,
    restructure_information_architecture,
)


def test_recursive_gradient_descent_order_is_deterministic() -> None:
    names = ["delta", "alpha", "charlie", "bravo"]
    order = recursive_gradient_descent_order([encode_entry(name) for name in names])
    assert [names[idx] for idx in order] == ["alpha", "delta", "bravo", "charlie"]


def test_restructure_information_architecture_respects_recursive_updates() -> None:
    blueprint = (
        ("station_a", "", ("gamma", "alpha", "beta")),
        ("station_b", "", ("delta", "charlie")),
        ("station_c", "", ("epsilon",)),
    )

    restructured = restructure_information_architecture(blueprint)
    names = [name for name, _, _ in restructured]
    assert names == ["station_a", "station_b", "station_c"]
    assert restructured[0][2] == ("beta", "gamma", "alpha")
    assert restructured[1][2] == ("delta", "charlie")
