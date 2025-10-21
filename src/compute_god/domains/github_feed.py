"""Model a lightweight GitHub mobile feed snapshot.

The repository already ships with a :class:`ScreenshotEnvironment` capable of
rendering a generic search surface.  The user story that motivated this module
asked for a concrete, data-friendly representation of the GitHub screen
described in the conversation log: a single repository card surfaced under the
``JS-KK`` profile and two recent issues collected from the subscriptions feed.

Rather than painting pixels directly, this module structures the information so
that other layers (renderers, narrators, or screenshot routines) can consume a
stable data model.  The intent is to make the domain concepts explicit:

* :class:`RepositoryCard` exposes basic metadata about a repository tile.
* :class:`IssueActivity` captures the status of an issue entry, including its
  labels and most recent state change.
* :class:`GitHubMobileFeed` ties everything together under the address bar shown
  in the screenshot.

The ``github_feed`` factory returns a fully-populated feed matching the details
outlined in the user's description.  Tests assert key fields so that future
refactors retain the narrative fidelity of the mocked interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple


@dataclass(frozen=True)
class RepositoryCard:
    """Repository information displayed in the mobile feed."""

    owner: str
    name: str
    excerpt: str
    stars: int
    license: str | None = None

    @property
    def slug(self) -> str:
        """Return the ``owner/name`` slug used across GitHub."""

        return f"{self.owner}/{self.name}" if self.owner else self.name

    @property
    def url(self) -> str:
        """Return the canonical web URL for the repository."""

        slug = self.slug
        return f"https://github.com/{slug}" if slug else "https://github.com"

    def summary(self) -> Mapping[str, object]:
        """Return a serialisable snapshot of the repository."""

        data = {
            "slug": self.slug,
            "excerpt": self.excerpt,
            "stars": int(self.stars),
        }
        if self.license is not None:
            data["license"] = self.license
        return data


@dataclass(frozen=True)
class IssueActivity:
    """Single issue card from the GitHub activity stream."""

    repository: str
    number: int
    title: str
    labels: Tuple[str, ...]
    status: str
    updated: str

    @property
    def reference(self) -> str:
        """Return the canonical ``owner/repo#number`` reference."""

        return f"{self.repository}#{self.number}"

    @property
    def url(self) -> str:
        """Return the public URL for the issue on github.com."""

        return f"https://github.com/{self.repository}/issues/{self.number}"

    def label_list(self) -> Tuple[str, ...]:
        """Expose the labels as a tuple to discourage accidental mutation."""

        return tuple(self.labels)

    def has_label(self, label: str) -> bool:
        """Return ``True`` when ``label`` is present on the issue."""

        return label in self.labels

    def summary(self) -> Mapping[str, object]:
        """Return a serialisable representation of the issue card."""

        return {
            "reference": self.reference,
            "title": self.title,
            "labels": list(self.labels),
            "status": self.status,
            "updated": self.updated,
        }


@dataclass(frozen=True)
class GitHubMobileFeed:
    """Container bundling the address bar, repositories and issue activity."""

    address: str
    repositories: Tuple[RepositoryCard, ...]
    issues: Tuple[IssueActivity, ...]

    def repository_slugs(self) -> Tuple[str, ...]:
        """Return the slugs for all repositories in display order."""

        return tuple(repo.slug for repo in self.repositories)

    def issue_references(self) -> Tuple[str, ...]:
        """Return the canonical references for issue cards in display order."""

        return tuple(issue.reference for issue in self.issues)

    def issues_for_repository(self, repository: str) -> Tuple[IssueActivity, ...]:
        """Return all issues in the feed belonging to ``repository``."""

        return tuple(issue for issue in self.issues if issue.repository == repository)

    def summary(self) -> Mapping[str, object]:
        """Return a serialisable view of the feed suitable for templating."""

        return {
            "address": self.address,
            "repositories": [repo.summary() for repo in self.repositories],
            "issues": [issue.summary() for issue in self.issues],
        }


def github_feed() -> GitHubMobileFeed:
    """Return a feed model that mirrors the described GitHub screen."""

    repositories: Tuple[RepositoryCard, ...] = (
        RepositoryCard(
            owner="JS-KK",
            name="google",
            excerpt="function(sttc){/* Copyright The Closure...",
            stars=30,
            license="Apache-2.0",
        ),
    )

    issues: Tuple[IssueActivity, ...] = (
        IssueActivity(
            repository="equinor/acidwatch",
            number=515,
            title="High input concentrations to ARCS in acidwatch crashes frontend",
            labels=("bug", "confirmed bug"),
            status="open",
            updated="2 hours ago",
        ),
        IssueActivity(
            repository="oven-sh/bun",
            number=23062,
            title="Does not work with pino-pretty",
            labels=("enhancement", "hacktoberfest"),
            status="open",
            updated="yesterday",
        ),
    )

    return GitHubMobileFeed(
        address="https://github.com/JS-KK/-",
        repositories=repositories,
        issues=issues,
    )


__all__ = [
    "GitHubMobileFeed",
    "IssueActivity",
    "RepositoryCard",
    "github_feed",
]

