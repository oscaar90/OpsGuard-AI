"""Security policy engine for OpsGuard-AI (ADR-0001: Local Gatekeeper Pattern)."""

import re
from pathlib import Path
from typing import List

import yaml


class SecurityPolicyError(Exception):
    """Custom exception for security policy errors."""

    pass


class SecurityPolicy:
    """Deterministic security scanner that checks diffs for hardcoded secrets.

    This class implements the Local Gatekeeper pattern (ADR-0001), scanning
    code diffs for blocklisted patterns before any LLM analysis occurs.
    """

    def __init__(self, config_path: str = "opsguard.yml") -> None:
        """Initialize SecurityPolicy with blocklist rules from configuration.

        Args:
            config_path: Path to the YAML configuration file.

        Raises:
            SecurityPolicyError: If config file is missing or invalid.
        """
        self.rules: List[dict] = []
        self._load_config(config_path)

    def _load_config(self, config_path: str) -> None:
        """Load security rules from YAML configuration file.

        Args:
            config_path: Path to the configuration file.

        Raises:
            SecurityPolicyError: If file is missing, unreadable, or invalid.
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise SecurityPolicyError(
                f"Configuration file not found: {config_path}"
            )

        try:
            content = config_file.read_text(encoding="utf-8")
            config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise SecurityPolicyError(f"Invalid YAML in configuration: {e}")
        except OSError as e:
            raise SecurityPolicyError(f"Failed to read configuration file: {e}")

        if not config or "blocklist" not in config:
            raise SecurityPolicyError(
                "Configuration must contain a 'blocklist' section"
            )

        blocklist = config["blocklist"]
        if not isinstance(blocklist, list):
            raise SecurityPolicyError("'blocklist' must be a list of rules")

        for rule in blocklist:
            if not isinstance(rule, dict):
                raise SecurityPolicyError("Each rule must be a dictionary")
            if "name" not in rule or "pattern" not in rule:
                raise SecurityPolicyError(
                    "Each rule must have 'name' and 'pattern' fields"
                )

            # Pre-compile regex for performance
            try:
                compiled = re.compile(rule["pattern"])
                self.rules.append({
                    "name": rule["name"],
                    "pattern": compiled,
                })
            except re.error as e:
                raise SecurityPolicyError(
                    f"Invalid regex in rule '{rule['name']}': {e}"
                )

    def scan_diff(self, diff_text: str) -> List[str]:
        """Scan a git diff for security violations.

        Only scans added lines (starting with '+') to detect new secrets.
        Deleted lines (starting with '-') are ignored as we only care
        about secrets being introduced, not removed.

        Args:
            diff_text: Raw git diff string to analyze.

        Returns:
            List of violation messages. Empty list if no violations found.
        """
        violations: List[str] = []

        if not diff_text:
            return violations

        # Extract only added lines (excluding diff headers like +++ )
        added_lines = []
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                # Remove the leading '+' for pattern matching
                added_lines.append(line[1:])

        # Join added lines for multiline pattern matching
        added_content = "\n".join(added_lines)

        # Check each rule against the added content
        for rule in self.rules:
            matches = rule["pattern"].findall(added_content)
            if matches:
                # Report each unique match
                for match in set(matches):
                    # Truncate long matches for readability
                    display_match = match if len(match) <= 40 else f"{match[:37]}..."
                    violations.append(
                        f"[{rule['name']}] Found pattern: {display_match}"
                    )

        return violations
