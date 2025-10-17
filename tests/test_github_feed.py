from compute_god.github_feed import GitHubMobileFeed, IssueActivity, RepositoryCard, github_feed


def test_github_feed_matches_expected_snapshot() -> None:
    feed = github_feed()

    assert isinstance(feed, GitHubMobileFeed)
    assert feed.address == "https://github.com/JS-KK/-"

    repositories = feed.repositories
    assert repositories == (
        RepositoryCard(
            owner="JS-KK",
            name="google",
            excerpt="function(sttc){/* Copyright The Closure...",
            stars=30,
            license="Apache-2.0",
        ),
    )

    repo = repositories[0]
    assert repo.slug == "JS-KK/google"
    assert repo.summary()["stars"] == 30

    issues = feed.issues
    assert issues == (
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

    assert feed.repository_slugs() == ("JS-KK/google",)
    assert feed.issue_references() == (
        "equinor/acidwatch#515",
        "oven-sh/bun#23062",
    )

    summary = feed.summary()
    assert summary["address"] == feed.address
    assert summary["repositories"][0]["license"] == "Apache-2.0"
    assert summary["issues"][1]["labels"] == ["enhancement", "hacktoberfest"]

