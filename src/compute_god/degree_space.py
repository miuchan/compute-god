"""Linear algebra helpers for playful "degree" spaces.

This module introduces a tiny algebra where states are treated as coordinates
over a labelled "degree" space.  The intent mirrors the rest of the project:
provide light‑weight, dependency free primitives that are still faithful to the
mathematical objects they evoke.  In this setting a :class:`DegreeSpace` stores
the coefficients of a vector, while :class:`DegreeDual` represents the
associated linear functional (its dual).  A negative dual simply flips the
orientation, matching the common convention of multiplying by ``-1``.

The key operation enabled by these helpers is forming tensor products of duals.
Given two dual functionals ``φ`` and ``ψ`` we can construct the tensor product
``φ ⊗ ψ`` which acts on pairs of vectors via ``(φ ⊗ ψ)(u, v) = φ(u) · ψ(v)``.
This is intentionally explicit so that callers can reason about the algebraic
structure without relying on an external linear algebra package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping, Tuple

State = MutableMapping[str, float]


def _coerce_mapping(degrees: Mapping[str, object] | Iterable[Tuple[str, object]]) -> dict[str, float]:
    """Normalise degree-like data into a ``dict`` of floats."""

    if hasattr(degrees, "items"):
        items = degrees.items()  # type: ignore[assignment]
    else:
        items = degrees

    coerced: dict[str, float] = {}
    for key, value in items:
        coerced[str(key)] = float(value)
    return coerced


class DegreeSpace:
    """Represent a labelled vector in the "degree" space."""

    __slots__ = ("_degrees",)

    def __init__(self, degrees: Mapping[str, object] | Iterable[Tuple[str, object]]):
        self._degrees = _coerce_mapping(degrees)

    def basis(self) -> Tuple[str, ...]:
        """Return the labels that span this space."""

        return tuple(self._degrees.keys())

    def coefficient(self, label: str) -> float:
        """Return the coordinate associated with ``label`` (defaults to ``0``)."""

        return self._degrees.get(label, 0.0)

    def as_state(self) -> State:
        """Return a defensive copy of the degrees as a mutable mapping."""

        return dict(self._degrees)

    # Dual helpers -----------------------------------------------------
    def dual(self) -> "DegreeDual":
        """Return the linear functional induced by the stored coordinates."""

        return DegreeDual(self._degrees)

    def negative_dual(self) -> "DegreeDual":
        """Return the dual with flipped orientation (multiplication by ``-1``)."""

        return DegreeDual(self._degrees, sign=-1.0)

    # Convenience protocol ---------------------------------------------
    def __iter__(self):  # pragma: no cover - convenience hook
        return iter(self._degrees)

    def __len__(self) -> int:  # pragma: no cover - trivial proxy
        return len(self._degrees)

    def __repr__(self) -> str:  # pragma: no cover - debugging friendly repr
        return f"DegreeSpace({self._degrees!r})"


@dataclass(frozen=True)
class DegreeDual:
    """Linear functional over a :class:`DegreeSpace`.

    Parameters
    ----------
    degrees:
        Mapping describing the coefficients of the dual functional.
    sign:
        Orientation multiplier.  ``1`` yields the standard dual while ``-1``
        gives the negative dual.  Other values are technically valid but the
        helper is primarily designed for ``±1``.
    """

    degrees: Mapping[str, float]
    sign: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "degrees", _coerce_mapping(self.degrees))

    def __call__(self, vector: Mapping[str, object] | DegreeSpace) -> float:
        """Evaluate the functional against ``vector``.

        ``vector`` can be either a raw mapping of coordinates or another
        :class:`DegreeSpace`.  Missing labels are treated as zeros so that the
        evaluation behaves well under partial bases.
        """

        if isinstance(vector, DegreeSpace):
            coordinates = vector.as_state()
        else:
            coordinates = _coerce_mapping(vector)

        total = 0.0
        for label, coefficient in self.degrees.items():
            total += coefficient * coordinates.get(label, 0.0)
        return self.sign * total

    def tensor(self, other: "DegreeDual") -> "DegreeTensor":
        """Return the tensor product ``self ⊗ other``."""

        return DegreeTensor(self, other)


@dataclass(frozen=True)
class DegreeTensor:
    """Tensor product of two dual functionals."""

    left: DegreeDual
    right: DegreeDual

    def __call__(
        self,
        left_vector: Mapping[str, object] | DegreeSpace,
        right_vector: Mapping[str, object] | DegreeSpace,
    ) -> float:
        """Evaluate ``(left ⊗ right)(left_vector, right_vector)``."""

        return self.left(left_vector) * self.right(right_vector)


def tensor_product(left: DegreeDual, right: DegreeDual) -> DegreeTensor:
    """Construct the tensor product of two duals."""

    return DegreeTensor(left, right)


__all__ = ["DegreeSpace", "DegreeDual", "DegreeTensor", "tensor_product"]

