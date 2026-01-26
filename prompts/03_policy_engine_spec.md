# Role
Act as a Senior Security Engineer.

# Context
We are implementing the "Local Gatekeeper" pattern (ADR-0001).
We need a deterministic security engine that scans code diffs for hardcoded secrets *before* any LLM analysis.

# Task 1: Configuration File (opsguard.yml)
Create a default configuration file named `opsguard.yml` in the root directory.
It must define a `blocklist` of regex patterns.
Include default patterns for:
- AWS Access Key (`AKIA...`)
- Generic Private Keys (`-----BEGIN RSA PRIVATE KEY-----`)
- GitHub Personal Access Tokens (`ghp_...`)

# Task 2: Security Module (src/security.py)
Create a class `SecurityPolicy` in `src/security.py`.
Requirements:
1.  **Load Config:** In `__init__`, load rules from `opsguard.yml` (use `pyyaml`). Handle generic/missing file errors.
2.  **Scan Method:** Implement `scan_diff(diff_text: str) -> List[str]`.
    - Input: The raw git diff string.
    - Logic: Iterate over all regex patterns in the blocklist against the diff.
    - Output: A list of found violation messages (e.g., "Found AWS Key pattern").
    - **Optimization:** Do not run regex on lines starting with `-` (deleted lines), only on `+` (added lines). We don't care if a secret is being removed, only if it's being added.

# Task 3: Update Main CLI (src/main.py)
Update the `scan` command:
1.  Initialize `SecurityPolicy`.
2.  Run `scan_diff` on the diff obtained from `GitManager`.
3.  **Hard Fail:** If violations are found:
    - Print them in RED (using Typer colors).
    - `sys.exit(1)` immediately. Do NOT proceed.
4.  If clean, print "Security Check Passed" in GREEN.

# Output Format
Provide the full code for:
1. `opsguard.yml`
2. `src/security.py`
3. `src/main.py` (updated)