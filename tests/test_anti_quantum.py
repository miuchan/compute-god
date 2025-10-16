import pytest

from compute_god import (
    AntiQuantumAlgorithm,
    AntiQuantumDual,
    QuantumAttackSurface,
    anti_quantum_dual,
    抗量子对偶,
)


def test_anti_quantum_dual_success():
    algorithm = AntiQuantumAlgorithm(
        name="Falcon-like",
        primitive="lattice",
        security_bits=256,
        noise_budget=0.12,
    )
    attack = QuantumAttackSurface(
        name="Grover boosted",
        quantum_speedup=8.0,
        required_security_bits=240,
        decoherence_rate=0.04,
    )

    dual = anti_quantum_dual(algorithm, attack)
    assert isinstance(dual, AntiQuantumDual)
    assert dual.algorithm is algorithm
    assert dual.attack is attack
    # Grover-like speedup of 8 -> subtract log2(8) = 3 bits.
    assert dual.effective_security_bits == 253.0
    assert dual.decoherence_margin == pytest.approx(0.08)
    # Duality index balances the security ratio and decoherence ratio.
    assert 0 < dual.duality_index <= 1


def test_anti_quantum_dual_failure_on_security():
    algorithm = AntiQuantumAlgorithm(
        name="Toy Scheme",
        primitive="hash",
        security_bits=128,
        noise_budget=0.1,
    )
    attack = QuantumAttackSurface(
        name="Amplified",
        quantum_speedup=32.0,
        required_security_bits=130,
        decoherence_rate=0.02,
    )

    assert anti_quantum_dual(algorithm, attack) is None


def test_chinese_alias():
    algorithm = AntiQuantumAlgorithm(
        name="Kyber-like",
        primitive="module-lattice",
        security_bits=192,
        noise_budget=0.06,
    )
    attack = QuantumAttackSurface(
        name="Surface",
        quantum_speedup=4.0,
        required_security_bits=170,
        decoherence_rate=0.08,
    )

    assert 抗量子对偶(algorithm, attack) is None

