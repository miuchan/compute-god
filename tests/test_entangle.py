from compute_god.entangle import (
    Chanzi,
    Entangler,
    EntanglementSnapshot,
    Jiuzi,
    纠子,
    缠子,
    纠缠子,
)


def _metric(a, b):
    return abs(a.get("value", 0) - b.get("value", 0))


def test_jiuzi_tracks_best_state():
    target = {"value": 10}
    jiuzi = Jiuzi(target_state=target, metric=_metric)

    assert jiuzi.observe({"value": 13}) == 3
    assert jiuzi.observe({"value": 9}) == 1

    strongest = jiuzi.strongest_state()
    assert strongest == {"value": 9}
    assert jiuzi.is_strong(1)


def test_chanzi_records_best_pair():
    chanzi = Chanzi(metric=_metric)
    assert chanzi.weave({"value": 5}, {"value": 8}) == 3
    assert chanzi.weave({"value": 7}, {"value": 6}) == 1

    best_left, best_right = chanzi.strongest_pair()
    assert best_left == {"value": 7}
    assert best_right == {"value": 6}
    assert chanzi.is_strong(1)


def test_entangler_combines_trackers():
    left = 纠子(target_state={"value": 2}, metric=_metric)
    right = 缠子(metric=_metric)

    # ``缠子`` without a reference is a ``Chanzi`` instance; build the entangler
    entangler = 纠缠子(left=left, right=Jiuzi(target_state={"value": 2}, metric=_metric), pair=right)

    snapshot = entangler.entangle({"value": 2}, {"value": 3})
    assert isinstance(snapshot, EntanglementSnapshot)
    assert snapshot.left_delta == 0
    assert snapshot.right_delta == 1
    assert snapshot.pair_delta == 1

    best = entangler.strongest_pair()
    assert best == ({"value": 2}, {"value": 3})
    assert entangler.is_strong(1)

