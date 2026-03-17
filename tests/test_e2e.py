"""
End-to-end integration tests for the OpsGuard pipeline (src/main.py).

These tests validate the full Two-Gate pipeline contract using Typer's CliRunner.
Both GitManager and AIEngine are mocked - no git repository or API access is needed.

Key behaviours validated:
  - Gate 1 blocks diffs containing AWS credentials (exit code 1).
  - Gate 2 blocks diffs with semantic vulnerabilities when AI returns BLOCK (exit code 1).
  - Clean diffs pass both gates and exit with code 0.
  - Without OPENROUTER_API_KEY, Gate 2 is skipped and the pipeline exits cleanly (code 0).
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from src.main import app

RUNNER = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures" / "vulnerable_app"


def _make_diff(content: str) -> str:
    """Simulate a git diff by prefixing every line with '+'."""
    return "\n".join(f"+{line}" for line in content.splitlines())


# ---------------------------------------------------------------------------
# TestEndToEnd
# ---------------------------------------------------------------------------


class TestEndToEnd:
    """Full pipeline integration tests using the Typer CLI runner."""

    def test_gate1_blocks_aws_credentials(self, monkeypatch, mocker):
        """Gate 1 must block a diff that contains AWS credentials (exit code 1).

        AIEngine.analyze_diff() must NOT be called when Gate 1 blocks.
        """
        aws_content = (FIXTURES / "aws_creds.env").read_text()
        aws_diff = _make_diff(aws_content)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        # Lazy imports in scan() resolve from the source modules, not from src.main
        mock_git_manager = mocker.patch("src.ingest.GitManager")
        instance = mock_git_manager.return_value
        instance.get_staged_files.return_value = ["aws_creds.env"]
        instance.get_diff.return_value = aws_diff

        mock_ai = mocker.patch("src.ai.AIEngine")

        result = RUNNER.invoke(app, ["scan"])

        assert result.exit_code == 1, (
            f"Expected exit code 1 (BLOCKED by Gate 1), got {result.exit_code}.\n"
            f"Output: {result.output}"
        )
        mock_ai.return_value.analyze_diff.assert_not_called()

    def test_gate2_blocks_sql_injection(self, monkeypatch, mocker):
        """Gate 2 must block a diff with SQL injection when AI returns BLOCK (exit code 1).

        Gate 1 passes SQL injection (semantic vulnerability), Gate 2 catches it.
        """
        sql_content = (FIXTURES / "legacy_login.py").read_text()
        sql_diff = _make_diff(sql_content)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        mock_git_manager = mocker.patch("src.ingest.GitManager")
        instance = mock_git_manager.return_value
        instance.get_staged_files.return_value = ["legacy_login.py"]
        instance.get_diff.return_value = sql_diff

        mock_ai = mocker.patch("src.ai.AIEngine")
        mock_ai.return_value.analyze_diff.return_value = {
            "verdict": "BLOCK",
            "risk_score": 8,
            "explanation": "SQL injection detected",
            "findings": ["SQL injection detected in legacy_login.py"],
        }

        result = RUNNER.invoke(app, ["scan"])

        assert result.exit_code == 1, (
            f"Expected exit code 1 (BLOCKED by Gate 2), got {result.exit_code}.\n"
            f"Output: {result.output}"
        )

    def test_clean_diff_passes_both_gates(self, monkeypatch, mocker):
        """A clean diff must pass Gate 1 and Gate 2 and exit with code 0."""
        clean_diff = "+ x = 1\n+ y = 2"

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        mock_git_manager = mocker.patch("src.ingest.GitManager")
        instance = mock_git_manager.return_value
        instance.get_staged_files.return_value = ["clean_module.py"]
        instance.get_diff.return_value = clean_diff

        mock_ai = mocker.patch("src.ai.AIEngine")
        mock_ai.return_value.analyze_diff.return_value = {
            "verdict": "APPROVE",
            "risk_score": 1,
            "explanation": "Clean",
            "findings": [],
        }

        result = RUNNER.invoke(app, ["scan"])

        assert result.exit_code == 0, (
            f"Expected exit code 0 (APPROVED), got {result.exit_code}.\n"
            f"Output: {result.output}"
        )

    def test_pipeline_without_api_key(self, monkeypatch, mocker):
        """Without OPENROUTER_API_KEY, Gate 2 is skipped and pipeline exits cleanly (code 0)."""
        clean_diff = "+ x = 1\n+ y = 2"

        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        mock_git_manager = mocker.patch("src.ingest.GitManager")
        instance = mock_git_manager.return_value
        instance.get_staged_files.return_value = ["clean_module.py"]
        instance.get_diff.return_value = clean_diff

        mock_ai = mocker.patch("src.ai.AIEngine")

        result = RUNNER.invoke(app, ["scan"])

        assert result.exit_code == 0, (
            f"Expected exit code 0 (Gate 2 skipped), got {result.exit_code}.\n"
            f"Output: {result.output}"
        )
        mock_ai.return_value.analyze_diff.assert_not_called()
