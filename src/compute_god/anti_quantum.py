"""Duality helpers for post-quantum algorithms.

The module introduces a tiny vocabulary for reasoning about the balance between
post-quantum (a.k.a. quantum-resistant) algorithms and their adversarial
models.  The goal is not to be physically accurate but to provide a playful,
yet structured, abstraction that mirrors the dual helpers available in other
modules such as :mod:`compute_god.jizi`.

Three small dataclasses are exposed:

``AntiQuantumAlgorithm``
    Describes the coarse characteristics of a quantum-resistant scheme.  The
    ``security_bits`` attribute captures the classical hardness of the scheme
    while ``noise_budget`` approximates how much error the implementation can
    tolerate before correctness is compromised.

``QuantumAttackSurface``
    Summarises the assumed capabilities of the attacker.  ``quantum_speedup``
    models the effective advantage of quantum algorithms over classical ones
    (for instance Grover's quadratic speedup) and ``decoherence_rate`` acts as
    the counter-force coming from the fragility of real quantum hardware.

``AntiQuantumDual``
    Represents the resulting equilibrium when a scheme faces a specific attack
    surface.  Two numbers describe the balance: ``effective_security_bits``
    tracks how many classical security bits survive after accounting for the
    quantum speedup, while ``decoherence_margin`` reports how much tolerance is
    left after discounting the adversary's decoherence rate.

The :func:`anti_quantum_dual` helper returns ``None`` whenever the scheme fails
to withstand the attack surface.  Otherwise an :class:`AntiQuantumDual`
instance is produced describing the balance.  The function deliberately keeps
the maths simple – the objective of the project is to provide a conceptual
scaffolding rather than a cryptographically accurate model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AntiQuantumAlgorithm:
    """Crude description of a quantum-resistant algorithm.

    Parameters
    ----------
    name:
        Human readable identifier of the algorithm.
    primitive:
        Rough family or mathematical primitive powering the scheme (e.g.
        ``"lattice"`` or ``"hash"``).  The value is purely descriptive but it
        helps when generating human facing summaries.
    security_bits:
        Claimed classical security measured in bits.
    noise_budget:
        How much implementation noise (expressed as a positive floating point
        tolerance) the algorithm can accommodate while still producing valid
        outputs.
    """

    name: str
    primitive: str
    security_bits: float
    noise_budget: float

    def __post_init__(self) -> None:
        if self.security_bits <= 0:
            raise ValueError("security_bits must be strictly positive")
        if self.noise_budget <= 0:
            raise ValueError("noise_budget must be strictly positive")


@dataclass(frozen=True)
class QuantumAttackSurface:
    """Characterisation of the adversarial quantum capabilities."""

    name: str
    quantum_speedup: float
    required_security_bits: float
    decoherence_rate: float

    def __post_init__(self) -> None:
        if self.quantum_speedup <= 0:
            raise ValueError("quantum_speedup must be strictly positive")
        if self.required_security_bits <= 0:
            raise ValueError("required_security_bits must be strictly positive")
        if self.decoherence_rate <= 0:
            raise ValueError("decoherence_rate must be strictly positive")


@dataclass(frozen=True)
class AntiQuantumDual:
    """Equilibrium produced by matching an algorithm with an attack surface."""

    algorithm: AntiQuantumAlgorithm
    attack: QuantumAttackSurface
    effective_security_bits: float
    decoherence_margin: float
    duality_index: float


def _effective_security(algorithm: AntiQuantumAlgorithm, attack: QuantumAttackSurface) -> float:
    """Return the remaining security bits after accounting for the speedup."""

    speedup_bits = math.log2(attack.quantum_speedup)
    return algorithm.security_bits - speedup_bits


def _decoherence_margin(algorithm: AntiQuantumAlgorithm, attack: QuantumAttackSurface) -> float:
    """Return the remaining noise budget after subtracting decoherence."""

    return algorithm.noise_budget - attack.decoherence_rate


def anti_quantum_dual(
    algorithm: AntiQuantumAlgorithm, attack: QuantumAttackSurface
) -> Optional[AntiQuantumDual]:
    """Evaluate whether ``algorithm`` withstands the provided attack surface.

    The dual is only returned when both the effective security bits and the
    decoherence margin remain above the requirements posed by the attacker.
    ``None`` is used to signal that the scheme falls short.
    """

    effective_security_bits = _effective_security(algorithm, attack)
    decoherence_margin = _decoherence_margin(algorithm, attack)

    if effective_security_bits < attack.required_security_bits:
        return None
    if decoherence_margin < 0:
        return None

    # ``duality_index`` provides a compact indicator balancing the security and
    # decoherence margins.  Values close to ``1`` mean the scheme sits right at
    # the boundary while values greater than ``1`` indicate comfortable margins.
    security_ratio = effective_security_bits / attack.required_security_bits
    decoherence_ratio = decoherence_margin / algorithm.noise_budget
    duality_index = min(security_ratio, decoherence_ratio)

    return AntiQuantumDual(
        algorithm=algorithm,
        attack=attack,
        effective_security_bits=effective_security_bits,
        decoherence_margin=decoherence_margin,
        duality_index=duality_index,
    )


# Playful Chinese aliases matching the tone of the project.
抗量子算法 = AntiQuantumAlgorithm
量子攻击面 = QuantumAttackSurface
抗量子对偶 = anti_quantum_dual


__all__ = [
    "AntiQuantumAlgorithm",
    "QuantumAttackSurface",
    "AntiQuantumDual",
    "anti_quantum_dual",
    "抗量子算法",
    "量子攻击面",
    "抗量子对偶",
]

