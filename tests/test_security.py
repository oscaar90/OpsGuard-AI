"""
Unit tests for the SecurityPolicy engine (src/security.py).

These tests validate the deterministic Gate 1 (regex) of the Two-Gate System,
using the same fixture files available in tests/fixtures/vulnerable_app/ for
manual demonstrations.

Key design insight validated here:
  - Gate 1 (regex) catches secrets with known structural patterns (AWS keys, tokens…).
  - Gate 2 (AI)    catches semantic vulnerabilities (SQL injection, logic backdoors…).
  The tests below document WHICH gate is responsible for WHAT, so the separation
  of concerns is explicit and verifiable.
"""

import pytest
from pathlib import Path

from src.security import SecurityPolicy, SecurityPolicyError

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
FIXTURES = Path(__file__).parent / "fixtures" / "vulnerable_app"
CONFIG = Path(__file__).parent.parent / "opsguard.yml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_diff(content: str) -> str:
    """Simulate a git diff by prefixing every line with '+'.

    OpsGuard's scan_diff() only inspects added lines (starting with '+'),
    so this helper converts raw file content into the format OpsGuard expects.
    """
    return "\n".join(f"+{line}" for line in content.splitlines())


# ---------------------------------------------------------------------------
# Policy loading
# ---------------------------------------------------------------------------
class TestSecurityPolicyLoading:
    """Verify that SecurityPolicy loads and validates its configuration."""

    def test_loads_real_config_successfully(self):
        policy = SecurityPolicy(config_path=str(CONFIG))
        assert len(policy.rules) > 0

    def test_raises_on_missing_config_file(self):
        with pytest.raises(SecurityPolicyError, match="not found"):
            SecurityPolicy(config_path="nonexistent.yml")

    def test_raises_when_blocklist_section_is_absent(self, tmp_path):
        bad = tmp_path / "bad.yml"
        bad.write_text("other_key: value\n")
        with pytest.raises(SecurityPolicyError, match="blocklist"):
            SecurityPolicy(config_path=str(bad))

    def test_raises_on_invalid_yaml(self, tmp_path):
        bad = tmp_path / "bad.yml"
        bad.write_text("blocklist: [\n  - unclosed bracket\n")
        with pytest.raises(SecurityPolicyError):
            SecurityPolicy(config_path=str(bad))


# ---------------------------------------------------------------------------
# Gate 1 - secrets caught by regex (should BLOCK)
# ---------------------------------------------------------------------------
class TestGate1SecretDetection:
    """Gate 1 must block files that contain hardcoded secrets with known patterns."""

    @pytest.fixture(autouse=True)
    def policy(self):
        self.policy = SecurityPolicy(config_path=str(CONFIG))

    def test_aws_access_key_triggers_violation(self):
        """aws_creds.env - contains AKIA* key matched by the AWS Access Key pattern."""
        content = (FIXTURES / "aws_creds.env").read_text()
        violations = self.policy.scan_diff(make_diff(content))

        assert len(violations) > 0, "Expected AWS key violation, got none"
        assert any(
            "AWS" in v for v in violations
        ), f"Violation must reference AWS rule. Got: {violations}"

    def test_aws_violation_message_contains_pattern_name(self):
        """Each violation message must include the rule name for audit traceability."""
        content = (FIXTURES / "aws_creds.env").read_text()
        violations = self.policy.scan_diff(make_diff(content))

        assert any("[AWS Access Key]" in v for v in violations)


# ---------------------------------------------------------------------------
# Gate 1 - semantic vulnerabilities NOT caught by regex (Gate 2 responsibility)
# ---------------------------------------------------------------------------
class TestGate1DoesNotOverreach:
    """Gate 1 must pass files whose vulnerabilities are semantic, not structural.

    These cases are intentionally handled by Gate 2 (AI). If Gate 1 incorrectly
    flags them, it means the regex is producing false positives that would slow
    down the pipeline without adding security value.
    """

    @pytest.fixture(autouse=True)
    def policy(self):
        self.policy = SecurityPolicy(config_path=str(CONFIG))

    def test_sql_injection_passes_gate1(self):
        """legacy_login.py - SQL injection is a logic flaw, not a secret.

        Gate 1 (regex) must PASS this file. Gate 2 (AI) is responsible for
        detecting the unsanitised f-string query.
        """
        content = (FIXTURES / "legacy_login.py").read_text()
        violations = self.policy.scan_diff(make_diff(content))

        assert violations == [], (
            f"SQL injection should reach Gate 2 (AI), not be blocked by Gate 1. "
            f"Got: {violations}"
        )

    def test_logic_backdoor_passes_gate1(self):
        """auth_middleware.py - developer backdoor is a semantic vulnerability.

        The X-DEBUG-MODE bypass cannot be detected by pattern matching alone.
        Gate 1 must let it through so Gate 2 (AI) can reason about the logic.
        """
        content = (FIXTURES / "auth_middleware.py").read_text()
        violations = self.policy.scan_diff(make_diff(content))

        assert violations == [], (
            f"Logic backdoor should reach Gate 2 (AI), not be blocked by Gate 1. "
            f"Got: {violations}"
        )

    def test_php_config_with_generic_password_passes_gate1(self):
        """config.php - generic password in PHP array syntax is not caught by regex.

        The PHP '=>' operator does not match the '=' / ':' assignment patterns
        in opsguard.yml. This is a known limitation of Gate 1; Gate 2 (AI)
        is responsible for detecting it via contextual reasoning.
        """
        content = (FIXTURES / "config.php").read_text()
        violations = self.policy.scan_diff(make_diff(content))

        assert (
            violations == []
        ), f"PHP generic password should reach Gate 2 (AI). Got: {violations}"

    def test_supply_chain_typosquatting_passes_gate1(self):
        """supply_chain_attack.py - typosquatting domain (ghrc.io vs ghcr.io).

        There is no deterministic regex pattern that can distinguish a legitimate
        domain from a typosquatted one. Gate 1 must pass this file; Gate 2 (AI)
        is responsible for detecting the anomaly via contextual reasoning about
        known registries and domain similarity.
        """
        content = (FIXTURES / "supply_chain_attack.py").read_text()
        violations = self.policy.scan_diff(make_diff(content))

        assert (
            violations == []
        ), f"Supply-chain typosquatting should reach Gate 2 (AI). Got: {violations}"


# ---------------------------------------------------------------------------
# Diff semantics
# ---------------------------------------------------------------------------
class TestDiffBehavior:
    """Validate correct handling of diff format edge cases."""

    @pytest.fixture(autouse=True)
    def policy(self):
        self.policy = SecurityPolicy(config_path=str(CONFIG))

    def test_deleted_lines_are_not_flagged(self):
        """Secrets on lines starting with '-' are being REMOVED - not introduced.

        Removing a secret is a remediation action. Flagging it would block
        the very commits that fix security issues.
        """
        diff = (
            "-AWS_ACCESS_KEY_ID=AKIAEXAMPLEACCESSKEY\n"
            "-AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        )
        violations = self.policy.scan_diff(diff)
        assert (
            violations == []
        ), f"Removed secrets must not be flagged. Got: {violations}"

    def test_diff_header_lines_are_ignored(self):
        """Lines starting with '+++' are diff metadata, not code."""
        diff = "+++ b/src/config.py\n+API_ENDPOINT = 'https://api.example.com'"
        violations = self.policy.scan_diff(diff)
        assert violations == []

    def test_empty_diff_returns_no_violations(self):
        assert self.policy.scan_diff("") == []

    def test_clean_python_code_returns_no_violations(self):
        diff = make_diff("def greet(name: str) -> str:\n    return f'Hello, {name}'")
        assert self.policy.scan_diff(diff) == []

    def test_multiple_secrets_in_one_diff_all_reported(self):
        """When a diff introduces multiple secrets, every one must be reported."""
        diff = (
            "+AWS_ACCESS_KEY_ID=AKIAEXAMPLEACCESSKEY\n"
            "+GITHUB_TOKEN=ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789A\n"
        )
        violations = self.policy.scan_diff(diff)
        assert (
            len(violations) >= 2
        ), f"Expected at least 2 violations, got {len(violations)}: {violations}"
