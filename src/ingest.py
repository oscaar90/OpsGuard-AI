"""Git ingestion module for OpsGuard-AI."""

import json
import os
from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError


class GitIngestError(Exception):
    """Custom exception for git ingestion errors."""

    pass


class GitManager:
    """Encapsulates gitpython operations for reading repository changes."""

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize GitManager with the repository path.

        Args:
            repo_path: Path to the git repository.

        Raises:
            GitIngestError: If the path is not a valid git repository.
        """
        try:
            self.repo = Repo(repo_path)
        except InvalidGitRepositoryError as e:
            raise GitIngestError(f"Invalid git repository at '{repo_path}': {e}")

    def is_ci(self) -> bool:
        """Check if running in GitHub Actions CI environment.

        Returns:
            True if GITHUB_ACTIONS environment variable is present.
        """
        return os.environ.get("GITHUB_ACTIONS") is not None

    def get_diff(self) -> str:
        """Get the git diff based on the execution environment.

        In local development (is_ci() == False):
            Returns diff against HEAD for uncommitted changes.

        In CI (GitHub Actions):
            Reads GITHUB_EVENT_PATH, parses the event JSON,
            and returns diff between pull_request.base.sha and pull_request.head.sha.

        Returns:
            The git diff as a string.

        Raises:
            GitIngestError: If unable to compute the diff.
        """
        if self.is_ci():
            return self._get_ci_diff()
        return self._get_local_diff()

    def _get_local_diff(self) -> str:
        """Get diff for local development (uncommitted changes against HEAD).

        Returns:
            The git diff output as a string.

        Raises:
            GitIngestError: If git diff command fails.
        """
        try:
            return self.repo.git.diff("HEAD")
        except GitCommandError as e:
            raise GitIngestError(f"Failed to get local diff: {e}")

    def _get_ci_diff(self) -> str:
        """Get diff for GitHub Actions CI environment.

        Reads the GitHub event payload to extract PR base and head SHAs.

        Returns:
            The git diff between base and head commits.

        Raises:
            GitIngestError: If event path is missing, JSON is invalid,
                           or required SHA values are not found.
        """
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if not event_path:
            raise GitIngestError("GITHUB_EVENT_PATH environment variable not set")

        event_file = Path(event_path)
        if not event_file.exists():
            raise GitIngestError(f"GitHub event file not found: {event_path}")

        try:
            event_data = json.loads(event_file.read_text())
        except json.JSONDecodeError as e:
            raise GitIngestError(f"Failed to parse GitHub event JSON: {e}")

        pull_request = event_data.get("pull_request")
        if not pull_request:
            raise GitIngestError("No pull_request data found in GitHub event")

        base_sha = pull_request.get("base", {}).get("sha")
        head_sha = pull_request.get("head", {}).get("sha")

        if not base_sha or not head_sha:
            raise GitIngestError(
                "Missing base.sha or head.sha in pull_request event data"
            )

        try:
            return self.repo.git.diff(base_sha, head_sha)
        except GitCommandError as e:
            raise GitIngestError(
                f"Failed to get diff between {base_sha} and {head_sha}: {e}"
            )
