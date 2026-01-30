import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError


class GitIngestError(Exception):
    """Custom exception for git ingestion errors."""
    pass


class GitManager:
    """Encapsulates gitpython operations for reading repository changes."""

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize GitManager with the repository path."""
        try:
            self.repo = Repo(repo_path)
        except InvalidGitRepositoryError as e:
            raise GitIngestError(f"Invalid git repository at '{repo_path}': {e}")

    def is_ci(self) -> bool:
        """Check if running in GitHub Actions CI environment."""
        return os.environ.get("GITHUB_ACTIONS") is not None

    def _get_ci_shas(self) -> Tuple[str, str]:
        """Helper: Extract base and head SHAs from GitHub Event JSON."""
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

        # --- FIX: DETECCIÓN DE EVENTOS NO-PR ---
        pull_request = event_data.get("pull_request")
        
        if not pull_request:
            # Si no hay objeto PR, verificamos si es un evento que debemos ignorar
            # (Merges a main, Deletes, Pushes directos)
            if "pusher" in event_data or "deleted" in event_data:
                 # Usamos una keyword específica "SKIP_SCAN" para capturarla en main
                 raise GitIngestError("SKIP_SCAN: Event is not a Pull Request (Push/Delete detected).")
            
            raise GitIngestError("No pull_request data found in GitHub event")

        base_sha = pull_request.get("base", {}).get("sha")
        head_sha = pull_request.get("head", {}).get("sha")

        if not base_sha or not head_sha:
            raise GitIngestError("Missing base.sha or head.sha in pull_request event data")
            
        return base_sha, head_sha

    def get_staged_files(self) -> List[str]:
        """Get list of changed filenames (for pre-filtering).

        Returns:
            List of file paths relative to repo root.
        """
        try:
            if self.is_ci():
                base_sha, head_sha = self._get_ci_shas()
                # Equivalent to: git diff --name-only base head
                diff_text = self.repo.git.diff(base_sha, head_sha, name_only=True)
            else:
                # Equivalent to: git diff --name-only HEAD
                diff_text = self.repo.git.diff("HEAD", name_only=True)
            
            return diff_text.splitlines() if diff_text else []
            
        except GitCommandError as e:
            raise GitIngestError(f"Failed to list staged files: {e}")

    def get_diff(self, files: Optional[List[str]] = None) -> str:
        """Get the git diff based on environment and strict file filtering.

        Args:
            files: Optional list of files to limit the diff to. 
                   If provided, only changes in these files are returned.

        Returns:
            The git diff as a string.
        """
        # Preparar argumentos extra para gitpython (file filtering)
        # git diff <commit> -- file1 file2
        extra_args = ["--"] + files if files else []

        if self.is_ci():
            return self._get_ci_diff(extra_args)
        return self._get_local_diff(extra_args)

    def _get_local_diff(self, extra_args: List[str]) -> str:
        """Get diff for local development."""
        try:
            # self.repo.git.diff("HEAD", "--", "file1", "file2")
            return self.repo.git.diff("HEAD", *extra_args)
        except GitCommandError as e:
            raise GitIngestError(f"Failed to get local diff: {e}")

    def _get_ci_diff(self, extra_args: List[str]) -> str:
        """Get diff for GitHub Actions CI environment."""
        base_sha, head_sha = self._get_ci_shas()

        try:
            return self.repo.git.diff(base_sha, head_sha, *extra_args)
        except GitCommandError as e:
            raise GitIngestError(
                f"Failed to get diff between {base_sha} and {head_sha}: {e}"
            )