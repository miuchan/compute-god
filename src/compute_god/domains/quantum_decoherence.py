"""Playful decoherence modelling for quantum mechanisms.

The goal of the module is not to provide a physically accurate simulation but
to offer a structured vocabulary for reasoning about decoherence within the
Compute-God universe.  A small catalogue of well-known mechanisms is provided
together with a lightweight environment model.  The helpers make it easy to
evaluate how a given experimental setup erodes the coherence of each mechanism
and to aggregate the results in a compact ledger.

``QuantumMechanism``
    Describes a single quantum capability that we want to track.  Each entry
    specifies the reference coherence time, its fragility and how many qubits
    typically participate in the effect.

``DecoherenceEnvironment``
    Captures the ambient conditions affecting the experiment.  The four
    floating point attributes are intentionally dimension-less so that callers
    can map them to whichever units make sense in their narratives.

``DecoherenceResult``
    Stores the outcome of running a mechanism through the environment model.
    The ``effective_coherence_time`` indicates how much usable coherence
    remains, while ``decoherence_rate`` expresses the corresponding decay rate
    normalised by the reference coherence time.

``DecoherenceLedger``
    Convenience container bundling all results together.  It offers a quick way
    to inspect which mechanism survives the longest and the overall decoherence
    budget required by the environment.

The mechanics aim to mirror the tone of neighbouring modules such as
``anti_quantum``: the emphasis is on storytelling-friendly ergonomics rather
than strict numerical accuracy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class QuantumMechanism:
    """Description of a quantum effect we want to decohere."""

    name: str
    description: str
    coherence_time: float
    fragility: float
    entanglement_order: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if self.coherence_time <= 0:
            raise ValueError("coherence_time must be strictly positive")
        if self.fragility <= 0:
            raise ValueError("fragility must be strictly positive")
        if self.entanglement_order <= 0:
            raise ValueError("entanglement_order must be at least one")


@dataclass(frozen=True)
class DecoherenceEnvironment:
    """Ambient conditions contributing to decoherence."""

    temperature: float
    magnetic_noise: float
    vibrational_noise: float
    cosmic_radiation: float

    def __post_init__(self) -> None:
        for field_name, value in (
            ("temperature", self.temperature),
            ("magnetic_noise", self.magnetic_noise),
            ("vibrational_noise", self.vibrational_noise),
            ("cosmic_radiation", self.cosmic_radiation),
        ):
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True)
class DecoherenceResult:
    """Outcome of evaluating a mechanism inside an environment."""

    mechanism: QuantumMechanism
    environment: DecoherenceEnvironment
    effective_coherence_time: float
    decoherence_rate: float
    noise_penalty: float


@dataclass(frozen=True)
class DecoherenceLedger:
    """Aggregate view of decoherence across multiple mechanisms."""

    environment: DecoherenceEnvironment
    results: Tuple[DecoherenceResult, ...]
    total_decoherence_rate: float

    def strongest_mechanism(self) -> DecoherenceResult | None:
        """Return the mechanism retaining the largest coherence time."""

        if not self.results:
            return None
        return max(self.results, key=lambda result: result.effective_coherence_time)

    def weakest_mechanism(self) -> DecoherenceResult | None:
        """Return the mechanism suffering the highest decoherence rate."""

        if not self.results:
            return None
        return max(self.results, key=lambda result: result.decoherence_rate)


def _environmental_noise(environment: DecoherenceEnvironment) -> float:
    """Combine the environment parameters into a single noise scalar."""

    thermal = environment.temperature / 300.0
    magnetic = environment.magnetic_noise
    vibrational = environment.vibrational_noise
    cosmic = environment.cosmic_radiation
    return thermal + magnetic + vibrational + cosmic


def _mechanism_penalty(mechanism: QuantumMechanism, environment: DecoherenceEnvironment) -> float:
    """Return the penalty factor induced by the environment on the mechanism."""

    environmental_noise = _environmental_noise(environment)
    entanglement_factor = math.log1p(mechanism.entanglement_order)
    penalty = environmental_noise * mechanism.fragility * entanglement_factor
    return max(0.0, penalty)


def decoherence_for_mechanism(
    mechanism: QuantumMechanism, environment: DecoherenceEnvironment
) -> DecoherenceResult:
    """Evaluate how ``mechanism`` decoheres inside ``environment``."""

    penalty = _mechanism_penalty(mechanism, environment)
    effective_coherence_time = mechanism.coherence_time / (1.0 + penalty)
    decoherence_rate = penalty / mechanism.coherence_time
    return DecoherenceResult(
        mechanism=mechanism,
        environment=environment,
        effective_coherence_time=effective_coherence_time,
        decoherence_rate=decoherence_rate,
        noise_penalty=penalty,
    )


KNOWN_QUANTUM_MECHANISMS: Tuple[QuantumMechanism, ...] = (
    QuantumMechanism(
        name="superposition",
        description="Single-qubit superposition held in a carefully isolated well.",
        coherence_time=120.0,
        fragility=1.0,
        entanglement_order=1,
    ),
    QuantumMechanism(
        name="entanglement",
        description="Bell-state style entanglement between two logical qubits.",
        coherence_time=90.0,
        fragility=1.4,
        entanglement_order=2,
    ),
    QuantumMechanism(
        name="quantum_tunneling",
        description="Macroscopic tunnelling maintained by superconducting junctions.",
        coherence_time=200.0,
        fragility=0.8,
        entanglement_order=1,
    ),
    QuantumMechanism(
        name="quantum_error_correction",
        description="Stabiliser code protecting logical information across many qubits.",
        coherence_time=320.0,
        fragility=0.65,
        entanglement_order=5,
    ),
    QuantumMechanism(
        name="topological_protection",
        description="Topological phase storing information in non-local degrees of freedom.",
        coherence_time=480.0,
        fragility=0.5,
        entanglement_order=4,
    ),
)


def decohere_all_known_quantum_mechanisms(
    environment: DecoherenceEnvironment,
) -> DecoherenceLedger:
    """Evaluate decoherence for the curated catalogue of mechanisms."""

    results = tuple(
        decoherence_for_mechanism(mechanism, environment)
        for mechanism in KNOWN_QUANTUM_MECHANISMS
    )
    total_rate = sum(result.decoherence_rate for result in results)
    return DecoherenceLedger(
        environment=environment,
        results=results,
        total_decoherence_rate=total_rate,
    )


# Playful Chinese alias mirroring neighbouring modules.
退相干所有量子机制 = decohere_all_known_quantum_mechanisms


__all__ = [
    "QuantumMechanism",
    "DecoherenceEnvironment",
    "DecoherenceResult",
    "DecoherenceLedger",
    "KNOWN_QUANTUM_MECHANISMS",
    "decoherence_for_mechanism",
    "decohere_all_known_quantum_mechanisms",
    "退相干所有量子机制",
]

