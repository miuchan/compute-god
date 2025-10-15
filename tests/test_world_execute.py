from compute_god import WorldExecutionRequest, world_execute


def test_world_execute_default():
    result = world_execute()
    assert result.converged is True
    assert result.universe.state["script"] == "world.execute(me);"
    assert result.universe.state["history"] == ["me", "world.execute(me);"]
    assert result.epochs == 2


def test_world_execute_custom_request():
    request = WorldExecutionRequest(
        subject="okabe",
        world="steins_gate",
        punctuation=".",
        history_key="timeline",
        script_key="phrase",
    )
    result = world_execute(request)
    assert result.universe.state["phrase"] == "steins_gate.execute(okabe)."
    assert result.universe.state["timeline"] == ["okabe", "steins_gate.execute(okabe)."]
    assert result.epochs == 2


def test_world_execute_custom_metric():
    calls = []

    def metric(prev, curr):
        calls.append((prev["script"], curr["script"]))
        return 0.0 if prev["script"] == curr["script"] else 42.0

    result = world_execute(metric=metric)
    assert result.converged is True
    assert calls == [
        ("me", "world.execute(me);"),
        ("world.execute(me);", "world.execute(me);"),
    ]
