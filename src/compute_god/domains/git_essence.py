"""Structured representation of Git's shared foundations and unique mechanics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple


@dataclass(frozen=True)
class GitConcept:
    """Base concept node used to organise Git's behaviour."""

    name: str
    synopsis: str

    def as_mapping(self) -> Mapping[str, object]:
        """Return a serialisable representation of the concept."""

        return {"name": self.name, "synopsis": self.synopsis}


@dataclass(frozen=True)
class GitCommonality(GitConcept):
    """Invariant qualities that apply to all Git workflows."""

    invariants: Tuple[str, ...]

    def as_mapping(self) -> Mapping[str, object]:
        data = super().as_mapping()
        data["invariants"] = list(self.invariants)
        return data


@dataclass(frozen=True)
class GitDifferentiator(GitConcept):
    """Mechanics that contrast Git with more traditional VCS models."""

    contrasts_with: str
    capabilities: Tuple[str, ...]

    def as_mapping(self) -> Mapping[str, object]:
        data = super().as_mapping()
        data.update(
            {
                "contrasts_with": self.contrasts_with,
                "capabilities": list(self.capabilities),
            }
        )
        return data


@dataclass(frozen=True)
class GitEssence:
    """Bundle Git's common ground and differentiating traits."""

    common_infrastructure: Tuple[GitCommonality, ...]
    differentiating_mechanics: Tuple[GitDifferentiator, ...]

    def common_names(self) -> Tuple[str, ...]:
        """Return the ordered names of the shared infrastructure blocks."""

        return tuple(concept.name for concept in self.common_infrastructure)

    def differentiator_names(self) -> Tuple[str, ...]:
        """Return the ordered names of the differentiating mechanics."""

        return tuple(concept.name for concept in self.differentiating_mechanics)

    def summary(self) -> Mapping[str, object]:
        """Return a serialisable overview linking shared and unique behaviour."""

        return {
            "common": [concept.as_mapping() for concept in self.common_infrastructure],
            "differentiators": [
                concept.as_mapping() for concept in self.differentiating_mechanics
            ],
        }


def git_essence_model() -> GitEssence:
    """Create a canonical model highlighting Git's nature."""

    common_infrastructure = (
        GitCommonality(
            name="Snapshot storage",
            synopsis="Git treats commits as complete filesystem snapshots.",
            invariants=(
                "Each commit references a tree object describing the project state.",
                "Unchanged files reuse existing blobs, emphasising immutability.",
            ),
        ),
        GitCommonality(
            name="Content addressed objects",
            synopsis="Git stores data in a hash-addressed object database.",
            invariants=(
                "Objects are retrieved by their cryptographic identifiers.",
                "Integrity checking falls out of the content hash design.",
            ),
        ),
        GitCommonality(
            name="Immutable history graph",
            synopsis="Commits form a DAG where parent references never change.",
            invariants=(
                "Rewriting history always produces new commits rather than editing old ones.",
                "Branch tips move while historical nodes remain intact until garbage collected.",
            ),
        ),
    )

    differentiating_mechanics = (
        GitDifferentiator(
            name="Branch pointers",
            synopsis="Branches are lightweight references to commits.",
            contrasts_with="Heavyweight branches in centralised VCS",
            capabilities=(
                "Cheap branching encourages experimental workflows.",
                "Merging or rebasing simply moves pointers across the history graph.",
            ),
        ),
        GitDifferentiator(
            name="Staging index",
            synopsis="The index acts as a sculptable layer before committing.",
            contrasts_with="Direct commit staging in traditional tools",
            capabilities=(
                "Partial commits via interactive staging refine history narration.",
                "Developers can review exact snapshots before sealing a commit.",
            ),
        ),
        GitDifferentiator(
            name="History rewriting commands",
            synopsis="Commands like rebase produce alternative commit sequences.",
            contrasts_with="Linear history editing",
            capabilities=(
                "Rebase rebuilds commits on top of new bases without mutating originals.",
                "Cherry-pick extracts specific changes into new contexts.",
            ),
        ),
        GitDifferentiator(
            name="Distributed synchronisation",
            synopsis="Every clone contains the full repository history.",
            contrasts_with="Central-server-only models",
            capabilities=(
                "Fetching and pushing exchange objects and pointers between peers.",
                "Offline work remains possible because clones are complete repositories.",
            ),
        ),
    )

    return GitEssence(
        common_infrastructure=common_infrastructure,
        differentiating_mechanics=differentiating_mechanics,
    )


__all__ = [
    "GitCommonality",
    "GitConcept",
    "GitDifferentiator",
    "GitEssence",
    "git_essence_model",
]
