"""许月明倒拔垂杨柳的技法建模。

The "倒拔垂杨柳" feat popularised in wuxia fiction describes an
effortlessly graceful yet brutally efficient manoeuvre: one uproots a willow
tree by gripping its hanging branches, reversing the tree's posture in a
single sweeping motion.  This module models that sequence with lightweight
data structures so that simulations can reason about leverage, rhythm, and the
order in which branches must be addressed.

The abstractions are intentionally simple:

* :class:`WillowBranch` captures a child branch together with the amount of
  resistance it offers during the manoeuvre.
* :class:`WeepingWillow` validates a tree structure, keeping track of parent
  relationships, depths, and helper queries such as ``path_to_root``.
* :class:`XuYuemingTechnique` quantifies the martial artist's grip strength,
  awareness of the root, and fluid footwork.  Calling
  :meth:`XuYuemingTechnique.uproot_weeping_willow` produces a
  :class:`WillowUprootPlan` that records the exact order of operations and the
  leverage applied on every node.

While whimsical, the helpers follow the repository's conventions: rich
docstrings, defensive copies where necessary, and deterministic ordering so
tests and downstream tooling can rely on reproducible outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class WillowBranch:
    """Relationship between a parent node and one of its branches.

    Parameters
    ----------
    child:
        Name of the downstream node.  Branch names must be unique within a
        :class:`WeepingWillow` so that the structure remains a tree.
    weight:
        Resistance associated with the branch.  ``0.0`` means the branch offers
        no resistance while larger numbers capture heavier or more entangled
        branches.  Negative weights are rejected because they would invert the
        physical meaning of the manoeuvre.
    """

    child: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.child:
            raise ValueError("WillowBranch child name must be non-empty")
        if self.weight < 0:
            raise ValueError("WillowBranch weight cannot be negative")


class WeepingWillow:
    """Finite rooted tree describing一株垂杨柳."""

    def __init__(self, root: str, branches: Mapping[str, Sequence[WillowBranch]]):
        if not root:
            raise ValueError("WeepingWillow root must be non-empty")
        self._root = root
        # Normalise the branch mapping while keeping deterministic order.
        normalised: Dict[str, Tuple[WillowBranch, ...]] = {
            parent: tuple(children) for parent, children in branches.items()
        }
        if root not in normalised:
            normalised[root] = tuple()

        parents: Dict[str, Tuple[str, float]] = {}
        for parent, children in list(normalised.items()):
            normalised[parent] = tuple(children)
            for branch in children:
                if branch.child in parents:
                    raise ValueError(f"Branch '{branch.child}' already has a parent")
                parents[branch.child] = (parent, branch.weight)
                normalised.setdefault(branch.child, tuple())

        # Breadth-first traversal ensures the structure forms a tree rooted at ``root``.
        visited = {root}
        queue = [root]
        while queue:
            current = queue.pop(0)
            for branch in normalised[current]:
                child = branch.child
                if child in visited:
                    raise ValueError("Willow structure must not contain cycles or duplicate children")
                visited.add(child)
                queue.append(child)

        # Check reachability of every declared node.
        unreachable = set(normalised) - visited
        if unreachable:
            raise ValueError(f"Unreachable branches: {sorted(unreachable)!r}")

        self._children = normalised
        self._parents = parents

    @property
    def root(self) -> str:
        """Return the name of the root node."""

        return self._root

    def children(self, node: str) -> Tuple[WillowBranch, ...]:
        """Return the children of ``node``."""

        return self._children[node]

    def nodes(self) -> Tuple[str, ...]:
        """Return all nodes in deterministic order (alphabetically)."""

        return tuple(sorted(self._children))

    def depth_map(self) -> Dict[str, int]:
        """Return the depth of every node measured from the root."""

        depths: Dict[str, int] = {self._root: 0}
        queue = [self._root]
        while queue:
            current = queue.pop(0)
            depth = depths[current] + 1
            for branch in self._children[current]:
                depths[branch.child] = depth
                queue.append(branch.child)
        return depths

    def branch_weight(self, node: str) -> float:
        """Return the resistance associated with ``node``'s incoming branch."""

        if node == self._root:
            return 0.0
        parent = self._parents.get(node)
        if parent is None:
            raise KeyError(f"Unknown node '{node}'")
        return float(parent[1])

    def parent(self, node: str) -> Optional[str]:
        """Return the parent node, or ``None`` if ``node`` is the root."""

        info = self._parents.get(node)
        if info is None:
            if node == self._root:
                return None
            raise KeyError(f"Unknown node '{node}'")
        return info[0]

    def path_to_root(self, node: str) -> Tuple[str, ...]:
        """Return the path from ``node`` back to the root (inclusive)."""

        if node not in self._children:
            raise KeyError(f"Unknown node '{node}'")
        path = [node]
        while node != self._root:
            parent = self.parent(node)
            assert parent is not None  # for type-checkers; root exits loop above
            path.append(parent)
            node = parent
        return tuple(path)

    def leaves(self) -> Tuple[str, ...]:
        """Return all leaf nodes sorted alphabetically."""

        return tuple(sorted(node for node, children in self._children.items() if not children))


@dataclass(frozen=True)
class UprootStep:
    """Single leverage application inside a :class:`WillowUprootPlan`."""

    node: str
    depth: int
    weight: float
    leverage: float


@dataclass(frozen=True)
class WillowUprootPlan:
    """Deterministic plan describing how许月明倒拔垂杨柳."""

    steps: Tuple[UprootStep, ...]
    total_effort: float

    def sequence(self) -> Tuple[str, ...]:
        """Return the order in which nodes are handled."""

        return tuple(step.node for step in self.steps)

    def leverage_profile(self) -> Tuple[Tuple[str, float], ...]:
        """Return a mapping-like tuple pairing nodes with leverage values."""

        return tuple((step.node, step.leverage) for step in self.steps)

    def node_leverage(self, node: str) -> float:
        """Return the leverage associated with ``node``."""

        for step in self.steps:
            if step.node == node:
                return step.leverage
        raise KeyError(f"Node '{node}' not present in plan")


class XuYuemingTechnique:
    """Quantify许月明的倒拔垂杨柳技巧。"""

    def __init__(self, grip_strength: float, root_awareness: float, *, footwork: float = 1.0):
        if grip_strength <= 0:
            raise ValueError("grip_strength must be positive")
        if footwork <= 0:
            raise ValueError("footwork must be positive")
        self.grip_strength = float(grip_strength)
        self.root_awareness = float(root_awareness)
        self.footwork = float(footwork)

    def _leverage(self, *, depth: int, weight: float) -> float:
        base = self.grip_strength / (1.0 + weight)
        awareness = self.root_awareness / (depth + 1.0)
        return (base + awareness) * self.footwork

    def uproot_weeping_willow(self, willow: WeepingWillow) -> WillowUprootPlan:
        """Compute the deterministic倒拔垂杨柳 plan for ``willow``."""

        depths = willow.depth_map()
        steps = []
        for node in sorted(depths, key=lambda item: (-depths[item], item)):
            weight = willow.branch_weight(node)
            leverage = self._leverage(depth=depths[node], weight=weight)
            steps.append(
                UprootStep(
                    node=node,
                    depth=depths[node],
                    weight=weight,
                    leverage=leverage,
                )
            )
        total_effort = sum(
            (step.weight + step.depth + 1.0) / step.leverage for step in steps
        )
        return WillowUprootPlan(steps=tuple(steps), total_effort=total_effort)

    倒拔垂杨柳 = uproot_weeping_willow


def 倒拔垂杨柳(technique: XuYuemingTechnique, willow: WeepingWillow) -> WillowUprootPlan:
    """Convenience wrapper mirroring the idiom in function form."""

    return technique.uproot_weeping_willow(willow)


许月明 = XuYuemingTechnique

__all__ = [
    "WillowBranch",
    "WeepingWillow",
    "XuYuemingTechnique",
    "WillowUprootPlan",
    "UprootStep",
    "倒拔垂杨柳",
    "许月明",
]
