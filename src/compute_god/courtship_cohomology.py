"""Cohomology for courtship rituals – whimsical yet precise.

The module frames the romantic metaphor of "seeking love" as a tiny cochain
complex.  Each cochain space stores symbolic qualities (confidence, empathy,
shared stories …) and the differentials describe how these qualities flow when
two people attempt to connect.  Once the linear maps are fixed we can compute
cohomology dimensions: the persistent patterns of tenderness that remain after
normalising for all small adjustments.

Despite the narrative flavour the implementation keeps the mathematics
honest.  All computations are performed with exact rational arithmetic to
avoid floating point artefacts.  This is useful when experimenting with small
illustrative complexes in teaching material or playful notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Iterable, List, Mapping, Tuple


FractionalMatrix = Tuple[Tuple[Fraction, ...], ...]


def _to_fraction(value: float | int | Fraction) -> Fraction:
    """Return ``value`` as a :class:`Fraction`.

    The helper accepts ``int`` and ``float`` inputs in addition to an existing
    :class:`Fraction`.  Floats are converted via ``Fraction(value).limit_denominator``
    so examples written with decimal coefficients remain readable yet exact.
    """

    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    return Fraction(value).limit_denominator()


@dataclass(frozen=True)
class CochainSpace:
    """A space of qualities that appear in a courtship story."""

    basis: Tuple[str, ...]

    def __post_init__(self) -> None:  # pragma: no cover - defensive guard
        if len({name.strip() for name in self.basis}) != len(self.basis):
            raise ValueError("basis names must be unique")

    @property
    def dimension(self) -> int:
        return len(self.basis)


@dataclass(frozen=True)
class CourtshipDifferential:
    """A linear map between two cochain spaces."""

    domain: int
    codomain: int
    matrix: FractionalMatrix

    def __post_init__(self) -> None:
        if not self.matrix:
            raise ValueError("matrix must contain at least one row")
        row_lengths = {len(row) for row in self.matrix}
        if len(row_lengths) != 1:
            raise ValueError("matrix rows must have equal length")

    @property
    def codomain_dimension(self) -> int:
        return len(self.matrix)

    @property
    def domain_dimension(self) -> int:
        return len(self.matrix[0]) if self.matrix else 0


def _row_reduce(matrix: FractionalMatrix) -> Tuple[FractionalMatrix, int]:
    """Return the row echelon form of ``matrix`` and its rank."""

    rows = [list(row) for row in matrix]
    num_rows = len(rows)
    num_cols = len(rows[0]) if rows else 0

    pivot_row = 0
    pivot_col = 0
    rank = 0

    while pivot_row < num_rows and pivot_col < num_cols:
        # Find pivot in current column.
        pivot = None
        for r in range(pivot_row, num_rows):
            if rows[r][pivot_col] != 0:
                pivot = r
                break

        if pivot is None:
            pivot_col += 1
            continue

        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        pivot_value = rows[pivot_row][pivot_col]

        # Normalise pivot row.
        rows[pivot_row] = [value / pivot_value for value in rows[pivot_row]]

        # Eliminate other rows.
        for r in range(num_rows):
            if r == pivot_row:
                continue
            factor = rows[r][pivot_col]
            if factor == 0:
                continue
            rows[r] = [value - factor * rows[pivot_row][c] for c, value in enumerate(rows[r])]

        pivot_row += 1
        pivot_col += 1
        rank += 1

    return tuple(tuple(entry for entry in row) for row in rows), rank


class CourtshipCochainComplex:
    """Finite cochain complex capturing a whimsical courtship dynamic."""

    def __init__(
        self,
        spaces: Mapping[int, CochainSpace],
        differentials: Iterable[CourtshipDifferential],
    ) -> None:
        self._spaces: Dict[int, CochainSpace] = dict(spaces)
        self._differentials: Dict[int, CourtshipDifferential] = {}

        for diff in differentials:
            matrix = tuple(tuple(_to_fraction(value) for value in row) for row in diff.matrix)
            diff = CourtshipDifferential(diff.domain, diff.codomain, matrix)
            self._validate_dimensions(diff)
            self._differentials[diff.domain] = diff

        self._validate_complex()

    def _validate_dimensions(self, diff: CourtshipDifferential) -> None:
        domain_dim = self._spaces[diff.domain].dimension
        codomain_dim = self._spaces[diff.codomain].dimension
        if diff.domain_dimension != domain_dim:
            raise ValueError(
                f"differential C^{diff.domain} -> C^{diff.codomain} has "
                f"domain dimension {diff.domain_dimension}, expected {domain_dim}"
            )
        if diff.codomain_dimension != codomain_dim:
            raise ValueError(
                f"differential C^{diff.domain} -> C^{diff.codomain} has "
                f"codomain dimension {diff.codomain_dimension}, expected {codomain_dim}"
            )

    def _validate_complex(self) -> None:
        for degree, diff in self._differentials.items():
            next_diff = self._differentials.get(diff.codomain)
            if next_diff is None:
                continue
            # Check that d_{k+1} ∘ d_k = 0 by verifying matrix multiplication is zero.
            composition = _matrix_multiply(next_diff.matrix, diff.matrix)
            if any(entry != 0 for row in composition for entry in row):
                raise ValueError(
                    f"d_{degree+1} ∘ d_{degree} is not zero; invalid cochain complex"
                )

    def space(self, degree: int) -> CochainSpace:
        return self._spaces[degree]

    def differential(self, degree: int) -> CourtshipDifferential | None:
        return self._differentials.get(degree)

    def cohomology_dimension(self, degree: int) -> int:
        """Return dim ker d_k − dim im d_{k-1}."""

        space = self._spaces[degree]
        d_k = self._differentials.get(degree)
        d_prev = self._differentials.get(degree - 1)

        kernel_dim = space.dimension
        if d_k is not None:
            _, rank = _row_reduce(d_k.matrix)
            kernel_dim -= rank

        image_dim = 0
        if d_prev is not None:
            _, image_rank = _row_reduce(d_prev.matrix)
            image_dim = image_rank

        result = kernel_dim - image_dim
        return max(result, 0)

    def betti_numbers(self) -> Dict[int, int]:
        """Return the Betti numbers indexed by degree."""

        return {degree: self.cohomology_dimension(degree) for degree in self._spaces}


def _matrix_multiply(a: FractionalMatrix, b: FractionalMatrix) -> FractionalMatrix:
    if not a or not b:
        return tuple()
    if len(b) != len(a[0]):
        raise ValueError("incompatible matrix dimensions for multiplication")

    result: List[List[Fraction]] = []
    for row_a in a:
        new_row: List[Fraction] = []
        for col in range(len(b[0])):
            entry = sum(row_a[k] * b[k][col] for k in range(len(b)))
            new_row.append(entry)
        result.append(new_row)
    return tuple(tuple(value for value in row) for row in result)


def courtship_cohomology_story(complex_: CourtshipCochainComplex) -> Dict[int, str]:
    """Return a small textual gloss for each non-vanishing cohomology degree."""

    story: Dict[int, str] = {}
    for degree, betti in complex_.betti_numbers().items():
        if betti == 0:
            continue
        basis = ", ".join(complex_.space(degree).basis)
        story[degree] = (
            f"H^{degree} has dimension {betti}; the enduring courtship patterns live "
            f"in the span of {{{basis}}}."
        )
    return story


__all__ = [
    "CochainSpace",
    "CourtshipCochainComplex",
    "CourtshipDifferential",
    "courtship_cohomology_story",
]

