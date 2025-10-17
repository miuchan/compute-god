"""Tests for the offline GitHub helpers."""

from __future__ import annotations

import pytest

from compute_god.github_offline import (
    IssueNotFound,
    OfflineGitHub,
    RepositoryNotFound,
    access_github,
)


def test_access_repository_card() -> None:
    client = OfflineGitHub()
    repository = client.get_repository("JS-KK", "google")

    description = access_github("https://github.com/JS-KK/google", client=client)
    assert repository.slug in description
    assert "Apache-2.0" in description


def test_access_issue_card() -> None:
    client = OfflineGitHub()
    issue = client.get_issue("oven-sh/bun", 23062)

    summary = access_github(
        "https://github.com/oven-sh/bun/issues/23062", client=client
    )
    assert issue.title in summary
    assert "hacktoberfest" in summary


def test_search_and_error_paths() -> None:
    client = OfflineGitHub()

    matches = client.search_repositories("closure")
    assert matches and matches[0].slug == "JS-KK/google"

    with pytest.raises(RepositoryNotFound):
        client.get_repository("unknown", "repo")

    with pytest.raises(IssueNotFound):
        client.get_issue("JS-KK/google", 999)

    assert access_github("https://github.com/JS-KK/-", client=client).startswith(
        "https://github.com/JS-KK/- hosts"
    )

