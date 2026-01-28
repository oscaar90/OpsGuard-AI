# Role
Act as a Principal AI Engineer.

# Context
We are upgrading OpsGuard-AI. Currently, it has a "Regex Gatekeeper" (Step 1).
Now, we need to implement "Step 2": The Contextual Analysis using Google Gemini 1.5 Flash.

# Task 1: Dependencies
Add `google-generativeai` to the project using poetry.

# Task 2: AI Engine (`src/ai.py`)
Create a class `AIEngine` that handles the interaction with Google's API.
* **Init:** Load `GEMINI_API_KEY` from environment variables. Raise an error if missing.
* **Configuration:** Use `gemini-1.5-flash`. Set temperature to `0.2` (we need determinism/precision, not creativity).
* **Method:** `analyze_diff(diff_text: str) -> dict`.

# Task 3: The System Prompt (The Core)
This is the most critical part. The LLM must act as a Senior Security Auditor.
* **Input:** A raw git diff.
* **Analysis Logic:**
    1.  Look for logical vulnerabilities (IDOR, Injection, weak auth).
    2.  Look for hardcoded secrets that the Regex might have missed (contextual secrets).
    3.  Look for dangerous bad practices (e.g., debug mode enabled in prod config).
* **Output Format:** PURE JSON. No markdown backticks.
    Schema:
    ```json
    {
      "risk_score": <int 0-10>,
      "verdict": "<APPROVE|BLOCK>",
      "issues": [
        {
          "type": "<Security|BestPractice|Performance>",
          "severity": "<Critical|High|Medium|Low>",
          "description": "<Concise explanation>",
          "file": "<guessed_filename_if_available>"
        }
      ]
    }
    ```

# Task 4: Update Main (`src/main.py`)
Update the `scan` workflow:
1.  Run Regex Check.
    * If FAIL -> Exit 1 (Existing behavior).
    * If PASS -> Continue to AI Check.
2.  Initialize `AIEngine`.
3.  Call `analyze_diff`.
4.  **Decision Logic:**
    * If `verdict` is "BLOCK" OR `risk_score` >= 7:
        * Print AI Findings in Red/Table format.
        * Exit 1.
    * Else:
        * Print "AI Analysis Passed" in Green.
        * Exit 0.

# Output Format
Provide the full code for:
1.  `src/ai.py`
2.  `src/main.py` (Updated)
3.  `pyproject.toml` (snippet with new dependency)