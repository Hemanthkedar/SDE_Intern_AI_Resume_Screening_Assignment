import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx

from app.models.result import GitHubResult


GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"

RECENT_REPO_DAYS = 90

ENGINEERING_EVENT_TYPES = {
    "PushEvent",
    "PullRequestEvent",
    "IssuesEvent",
    "IssueCommentEvent",
    "CreateEvent",
    "ReleaseEvent",
}


@dataclass
class GitHubProfile:
    username: str
    repositories: list[dict]
    events: list[dict]


class GitHubEnricher:
    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN")
        self._cache: dict[str, GitHubResult] = {}

    def enrich(self, github_url: str | None) -> GitHubResult:
        if not github_url:
            return GitHubResult(
                status="not_available",
                score=0,
                summary="No GitHub profile found in resume.",
            )

        username = self._extract_username(github_url)

        if not username:
            return GitHubResult(
                status="invalid_url",
                score=0,
                summary="GitHub URL could not be parsed.",
            )

        if username in self._cache:
            return self._cache[username]

        try:
            profile = self._fetch_profile(username)
            result = self._calculate_score(profile)

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            if status == 404:
                result = GitHubResult(
                    status="not_found",
                    score=0,
                    summary="GitHub profile was not found.",
                )
            elif status in {403, 429}:
                result = GitHubResult(
                    status="rate_limited",
                    score=0,
                    summary="GitHub API rate limit reached.",
                )
            else:
                result = GitHubResult(
                    status="api_error",
                    score=0,
                    summary=f"GitHub API returned HTTP {status}.",
                )

        except (httpx.HTTPError, ValueError) as exc:
            result = GitHubResult(
                status="failed",
                score=0,
                summary=f"GitHub enrichment failed: {exc}",
            )

        self._cache[username] = result
        return result

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def _fetch_profile(self, username: str) -> GitHubProfile:
        timeout = httpx.Timeout(10.0)

        with httpx.Client(
            base_url=GITHUB_API_BASE,
            headers=self._headers(),
            timeout=timeout,
        ) as client:

            repos_response = client.get(
                f"/users/{username}/repos",
                params={
                    "sort": "updated",
                    "per_page": 20,
                    "type": "owner",
                },
            )
            repos_response.raise_for_status()

            events_response = client.get(
                f"/users/{username}/events/public",
                params={"per_page": 30},
            )
            events_response.raise_for_status()

            return GitHubProfile(
                username=username,
                repositories=repos_response.json(),
                events=events_response.json(),
            )

    def _calculate_score(
        self,
        profile: GitHubProfile,
    ) -> GitHubResult:
        activity_score = self._activity_score(profile.events)
        repository_score = self._repository_score(
            profile.repositories
        )

        score = min(
            activity_score + repository_score,
            10,
        )

        if score == 0:
            summary = (
                "No meaningful recent public engineering activity "
                "or relevant maintained repositories detected."
            )
        else:
            summary = (
                f"Recent activity score: {activity_score}/5; "
                f"repository score: {repository_score}/5."
            )

        return GitHubResult(
            status="success",
            score=score,
            summary=summary,
        )

    @staticmethod
    def _activity_score(events: list[dict]) -> int:
        engineering_events = [
            event
            for event in events
            if event.get("type") in ENGINEERING_EVENT_TYPES
        ]

        count = len(engineering_events)

        if count == 0:
            return 0
        if count <= 2:
            return 1
        if count <= 5:
            return 2
        if count <= 9:
            return 3
        if count <= 14:
            return 4

        return 5

    @staticmethod
    def _repository_score(
        repositories: list[dict],
    ) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=RECENT_REPO_DAYS
        )

        relevant_repositories = 0

        for repo in repositories:
            if repo.get("fork"):
                continue

            if repo.get("archived"):
                continue

            pushed_at = repo.get("pushed_at")

            if not pushed_at:
                continue

            try:
                pushed = datetime.fromisoformat(
                    pushed_at.replace("Z", "+00:00")
                )
            except ValueError:
                continue

            if pushed < cutoff:
                continue

            language = (repo.get("language") or "").lower()
            topics = " ".join(repo.get("topics") or []).lower()
            name = (repo.get("name") or "").lower()
            description = (repo.get("description") or "").lower()

            searchable = (
                f"{language} {topics} {name} {description}"
            )

            if any(
                signal in searchable
                for signal in (
                    "python",
                    "fastapi",
                    "django",
                    "flask",
                    "ai",
                    "llm",
                    "langchain",
                    "langgraph",
                    "rag",
                    "machine learning",
                    "backend",
                )
            ):
                relevant_repositories += 1

        if relevant_repositories == 0:
            return 0
        if relevant_repositories == 1:
            return 2
        if relevant_repositories == 2:
            return 3
        if relevant_repositories <= 4:
            return 4

        return 5

    @staticmethod
    def _extract_username(url: str) -> str | None:
        try:
            parsed = urlparse(url.strip())

            if parsed.netloc.lower() not in {
                "github.com",
                "www.github.com",
            }:
                return None

            path_parts = [
                part
                for part in parsed.path.strip("/").split("/")
                if part
            ]

            if not path_parts:
                return None

            return path_parts[0]

        except Exception:
            return None