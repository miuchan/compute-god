"""Offline helpers that emulate a tiny slice of GitHub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .github_feed import GitHubMobileFeed, IssueActivity, RepositoryCard, github_feed


class RepositoryNotFound(LookupError):
    """Raised when a repository cannot be found in the offline index."""


class IssueNotFound(LookupError):
    """Raised when an issue cannot be found in the offline index."""


@dataclass
class OfflineGitHub:
    """Small in-memory model of the GitHub data described in :mod:`github_feed`."""

    feed: GitHubMobileFeed

    def __init__(self, feed: GitHubMobileFeed | None = None) -> None:
        self.feed = feed if feed is not None else github_feed()
        self._repository_index = {repo.slug: repo for repo in self.feed.repositories}
        self._issue_index = {
            (issue.repository, issue.number): issue for issue in self.feed.issues
        }

    def repositories(self) -> Tuple[RepositoryCard, ...]:
        """Return all repositories available in the feed."""

        return self.feed.repositories

    def issues(self) -> Tuple[IssueActivity, ...]:
        """Return all issue cards available in the feed."""

        return self.feed.issues

    def get_repository(self, owner: str, name: str | None = None) -> RepositoryCard:
        """Return a repository entry, raising :class:`RepositoryNotFound` otherwise."""

        slug = f"{owner}/{name}" if name is not None else owner
        try:
            return self._repository_index[slug]
        except KeyError as exc:  # pragma: no cover - defensive path
            raise RepositoryNotFound(slug) from exc

    def get_issue(self, repository: str, number: int) -> IssueActivity:
        """Return an issue entry, raising :class:`IssueNotFound` otherwise."""

        key = (repository, int(number))
        try:
            return self._issue_index[key]
        except KeyError as exc:  # pragma: no cover - defensive path
            raise IssueNotFound(f"{repository}#{number}") from exc

    def search_repositories(self, query: str) -> Tuple[RepositoryCard, ...]:
        """Return repositories whose slug or excerpt contains ``query``."""

        needle = query.strip().lower()
        if not needle:
            return ()

        matches: list[RepositoryCard] = []
        for repository in self.feed.repositories:
            haystack = f"{repository.slug} {repository.excerpt}".lower()
            if needle in haystack:
                matches.append(repository)
        return tuple(matches)

    def list_issues(self, repository: str | None = None) -> Tuple[IssueActivity, ...]:
        """Return issues belonging to ``repository`` or all issues when ``None``."""

        if repository is None:
            return self.feed.issues
        return tuple(issue for issue in self.feed.issues if issue.repository == repository)

    def describe_feed(self) -> str:
        """Return a human-readable summary of the available feed."""

        repositories = self.feed.repositories
        issues = self.feed.issues
        repo_count = len(repositories)
        issue_count = len(issues)
        return (
            f"{self.feed.address} hosts {repo_count} repository card(s) and "
            f"{issue_count} issue(s)."
        )


def access_github(url: str, *, client: OfflineGitHub | None = None) -> str:
    """Attempt to resolve ``url`` using the offline GitHub model."""

    instance = client if client is not None else OfflineGitHub()
    candidate = url.strip()
    if not candidate:
        return instance.describe_feed()

    if candidate.rstrip("/") == instance.feed.address.rstrip("/"):
        return instance.describe_feed()

    prefix = "https://github.com/"
    if not candidate.startswith(prefix):
        raise ValueError(f"Unsupported URL: {url!r}")

    path = candidate[len(prefix) :].strip("/")
    if not path:
        return instance.describe_feed()

    segments = path.split("/")
    if len(segments) == 2:
        repository = instance.get_repository(segments[0], segments[1])
        return (
            f"Repository {repository.slug}: {repository.excerpt} "
            f"(★ {repository.stars}, license={repository.license or 'n/a'})"
        )

    if len(segments) == 4 and segments[2] == "issues":
        issue = instance.get_issue(f"{segments[0]}/{segments[1]}", int(segments[3]))
        labels = ", ".join(issue.labels) if issue.labels else "no labels"
        return (
            f"Issue {issue.reference}: {issue.title} "
            f"[{labels}] – status: {issue.status}, updated {issue.updated}"
        )

    raise ValueError(f"Unsupported GitHub path: {path!r}")


__all__ = [
    "OfflineGitHub",
    "IssueNotFound",
    "RepositoryNotFound",
    "access_github",
]

