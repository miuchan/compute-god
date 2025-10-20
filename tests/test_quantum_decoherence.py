import pytest

from compute_god import (
    KNOWN_QUANTUM_MECHANISMS,
    DecoherenceEnvironment,
    decohere_all_known_quantum_mechanisms,
    decoherence_for_mechanism,
    退相干所有量子机制,
)


def test_decoherence_for_mechanism_reduces_coherence_time():
    environment = DecoherenceEnvironment(
        temperature=40.0,
        magnetic_noise=0.02,
        vibrational_noise=0.01,
        cosmic_radiation=0.005,
    )
    mechanism = KNOWN_QUANTUM_MECHANISMS[0]

    result = decoherence_for_mechanism(mechanism, environment)

    assert result.mechanism is mechanism
    assert result.environment is environment
    assert result.effective_coherence_time < mechanism.coherence_time
    assert result.decoherence_rate > 0
    # The ratio between reference and effective coherence time is 1 + penalty.
    expected_ratio = (mechanism.coherence_time / result.effective_coherence_time)
    assert expected_ratio == pytest.approx(1 + result.noise_penalty)


def test_environment_rejects_negative_parameters():
    with pytest.raises(ValueError):
        DecoherenceEnvironment(
            temperature=-1.0,
            magnetic_noise=0.0,
            vibrational_noise=0.0,
            cosmic_radiation=0.0,
        )


def test_catalogue_decoherence_uses_all_mechanisms():
    environment = DecoherenceEnvironment(
        temperature=20.0,
        magnetic_noise=0.01,
        vibrational_noise=0.03,
        cosmic_radiation=0.02,
    )

    ledger = decohere_all_known_quantum_mechanisms(environment)

    assert len(ledger.results) == len(KNOWN_QUANTUM_MECHANISMS)
    assert ledger.environment is environment
    assert ledger.total_decoherence_rate == pytest.approx(
        sum(result.decoherence_rate for result in ledger.results)
    )

    # The strongest mechanism should have the largest effective coherence time.
    strongest = ledger.strongest_mechanism()
    assert strongest is not None
    assert strongest.effective_coherence_time == max(
        result.effective_coherence_time for result in ledger.results
    )

    # Alias mirrors the main helper.
    alias_ledger = 退相干所有量子机制(environment)
    assert alias_ledger == ledger


def test_known_mechanisms_are_sorted_by_definition_order():
    environment = DecoherenceEnvironment(
        temperature=10.0,
        magnetic_noise=0.0,
        vibrational_noise=0.0,
        cosmic_radiation=0.0,
    )
    ledger = decohere_all_known_quantum_mechanisms(environment)
    names = [result.mechanism.name for result in ledger.results]
    assert names == [mechanism.name for mechanism in KNOWN_QUANTUM_MECHANISMS]

