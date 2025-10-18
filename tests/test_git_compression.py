from __future__ import annotations

from compute_god.git_compression import (
    GitObjectProfile,
    git_friendly_algorithms,
    known_compression_algorithms,
    plan_repository_compression,
)


def test_known_algorithms_include_git_defaults() -> None:
    algorithms = known_compression_algorithms()
    names = {algorithm.name for algorithm in algorithms}
    assert {"zlib", "zstd", "lz4"}.issubset(names)


def test_git_friendly_algorithms_filter_experimental_entries() -> None:
    friendly = git_friendly_algorithms()
    assert friendly  # sanity check
    assert all(algorithm.git_support for algorithm in friendly)
    # brotli appears in the catalogue but is not part of Git's backends yet
    assert "brotli" not in {algorithm.name for algorithm in friendly}


def test_plan_repository_compression_matches_profiles() -> None:
    algorithms = known_compression_algorithms()
    profiles = [
        GitObjectProfile(
            path="docs/whitepaper.md",
            kind="blob",
            size=2_000_000,
            redundancy=0.9,
            update_frequency=0.3,
            dictionary_candidate=True,
        ),
        GitObjectProfile(
            path="assets/logo.png",
            kind="blob",
            size=250_000,
            redundancy=0.1,
            update_frequency=0.1,
        ),
        GitObjectProfile(
            path="src/config.json",
            kind="blob",
            size=8_192,
            redundancy=0.7,
            update_frequency=0.95,
            dictionary_candidate=True,
        ),
    ]

    plan = plan_repository_compression(profiles, algorithms)

    assert plan.selection["docs/whitepaper.md"].name == "zstd"
    assert plan.selection["src/config.json"].name == "lz4"
    assert plan.estimated_sizes["docs/whitepaper.md"] < profiles[0].size
    assert plan.total_estimated_bytes() < sum(profile.size for profile in profiles)
    explanation = plan.explain("docs/whitepaper.md")
    assert "redundancy" in explanation
