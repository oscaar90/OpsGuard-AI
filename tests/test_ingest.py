"""
Unit tests for the GitManager and git ingestion module (src/ingest.py).

These tests validate the deterministic logic of the ingestion layer:
- Repository initialisation (valid / invalid path)
- Environment detection (CI vs local development)
- GitHub event JSON parsing for the CI code path

All tests are fully deterministic and run without network access,
API keys, or a running GitHub Actions environment. GitHub event
payloads are simulated using tmp_path JSON fixtures and monkeypatch.

Key behaviours validated:
  - SkipScanSignal is raised (not GitIngestError) for push/delete events,
    allowing main.py to exit cleanly with code 0 instead of failing.
  - _get_ci_shas() fails clearly with actionable messages for every
    misconfiguration scenario (missing env var, bad JSON, missing SHAs…).
  - SkipScanSignal is a subclass of GitIngestError - it can be caught
    by callers that only handle the base exception.
"""

import json

import pytest
from pathlib import Path

from src.ingest import GitManager, GitIngestError, SkipScanSignal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_event(tmp_path: Path, payload: dict) -> str:
    """Write a GitHub Actions event JSON file and return its path."""
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(payload))
    return str(event_file)


# ---------------------------------------------------------------------------
# GitManager initialisation
# ---------------------------------------------------------------------------


class TestGitManagerInit:
    """GitManager must accept a valid repository and fail clearly on bad input."""

    def test_initializes_with_valid_repo(self):
        """The project root is a valid git repository - init must succeed."""
        manager = GitManager(repo_path=".")
        assert manager.repo is not None

    def test_raises_on_invalid_repo_path(self, tmp_path):
        """A plain directory without .git must raise GitIngestError."""
        with pytest.raises(GitIngestError, match="Invalid git repository"):
            GitManager(repo_path=str(tmp_path))


# ---------------------------------------------------------------------------
# CI environment detection
# ---------------------------------------------------------------------------


class TestCIDetection:
    """is_ci() must reflect the presence of the GITHUB_ACTIONS environment variable."""

    def test_is_ci_returns_true_when_env_set(self, monkeypatch):
        """GITHUB_ACTIONS=true → running inside GitHub Actions."""
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        manager = GitManager(repo_path=".")
        assert manager.is_ci() is True

    def test_is_ci_returns_false_when_env_absent(self, monkeypatch):
        """Absent GITHUB_ACTIONS → local development context."""
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        manager = GitManager(repo_path=".")
        assert manager.is_ci() is False


# ---------------------------------------------------------------------------
# GitHub event JSON parsing - _get_ci_shas()
# ---------------------------------------------------------------------------


class TestCISHAParsing:
    """_get_ci_shas() must parse GitHub event payloads correctly and fail clearly."""

    @pytest.fixture
    def manager(self):
        return GitManager(repo_path=".")

    # --- Configuration errors ---

    def test_raises_when_event_path_not_set(self, manager, monkeypatch):
        """Missing GITHUB_EVENT_PATH is a CI misconfiguration - raise GitIngestError."""
        monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
        with pytest.raises(GitIngestError, match="GITHUB_EVENT_PATH"):
            manager._get_ci_shas()

    def test_raises_when_event_file_missing(self, manager, monkeypatch, tmp_path):
        """GITHUB_EVENT_PATH pointing to a non-existent file must raise GitIngestError."""
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(tmp_path / "missing.json"))
        with pytest.raises(GitIngestError, match="not found"):
            manager._get_ci_shas()

    def test_raises_on_invalid_json(self, manager, monkeypatch, tmp_path):
        """Malformed event JSON must raise GitIngestError with a parse error message."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ not valid json }")
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(bad_file))
        with pytest.raises(GitIngestError, match="Failed to parse"):
            manager._get_ci_shas()

    # --- SkipScanSignal: events that must be silently skipped ---

    def test_raises_skip_signal_on_push_event(self, manager, monkeypatch, tmp_path):
        """A push to main (has 'pusher', no 'pull_request') must raise SkipScanSignal.

        OpsGuard only analyses Pull Requests. Direct pushes to main are
        legitimate events that should exit cleanly with code 0, not fail.
        """
        payload = {"pusher": {"name": "oscaar90"}, "ref": "refs/heads/main"}
        monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
        with pytest.raises(SkipScanSignal):
            manager._get_ci_shas()

    def test_raises_skip_signal_on_branch_delete_event(
        self, manager, monkeypatch, tmp_path
    ):
        """A branch deletion event (has 'deleted' key) must raise SkipScanSignal."""
        payload = {"deleted": True, "ref": "refs/heads/old-feature"}
        monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
        with pytest.raises(SkipScanSignal):
            manager._get_ci_shas()

    def test_skip_scan_signal_is_subclass_of_git_ingest_error(self):
        """SkipScanSignal must be catchable as GitIngestError for callers that
        only handle the base exception class.
        """
        assert issubclass(SkipScanSignal, GitIngestError)

    # --- GitIngestError: events with unexpected structure ---

    def test_raises_when_no_pull_request_and_no_skip_trigger(
        self, manager, monkeypatch, tmp_path
    ):
        """An unknown event without 'pull_request', 'pusher', or 'deleted' is
        an unrecognised payload - raise GitIngestError (not SkipScanSignal).
        """
        payload = {"action": "some_unknown_action"}
        monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
        with pytest.raises(GitIngestError, match="No pull_request data"):
            manager._get_ci_shas()

    def test_raises_when_pull_request_missing_base_sha(
        self, manager, monkeypatch, tmp_path
    ):
        """PR event without base.sha / head.sha is malformed - raise GitIngestError."""
        payload = {"pull_request": {"title": "Incomplete PR payload"}}
        monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
        with pytest.raises(GitIngestError, match="Missing base.sha or head.sha"):
            manager._get_ci_shas()

    # --- Happy path ---

    def test_returns_correct_shas_from_valid_pr_event(
        self, manager, monkeypatch, tmp_path
    ):
        """A well-formed PR event must return (base_sha, head_sha) as strings."""
        payload = {
            "pull_request": {
                "base": {"sha": "abc1234deadbeef"},
                "head": {"sha": "def5678cafebabe"},
            }
        }
        monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
        base, head = manager._get_ci_shas()
        assert base == "abc1234deadbeef"
        assert head == "def5678cafebabe"
