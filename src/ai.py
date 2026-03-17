import os
import json
import time
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import box

load_dotenv()

_console = Console()


class AIEngineError(Exception):
    """Custom exception for AI Engine failures."""

    pass


# --- FINOPS CONFIGURATION (Unit Economic) ---
# Pricing for google/gemini-2.0-flash-001 (OpenRouter/Google pricing)
PRICE_PER_1M_INPUT = 0.10
PRICE_PER_1M_OUTPUT = 0.40

# --- DIFF PROCESSING LIMITS ---
# Max characters sent to the LLM to control cost and avoid context window overflow.
# Gemini Flash 2.0 supports ~1M tokens, but large diffs increase cost and latency.
MAX_DIFF_CHARS = 30_000

# --- TELEMETRY MODE (ADR-0003) ---
# Controls verbosity of FinOps and performance output.
# Configure via OPSGUARD_TELEMETRY_MODE: verbose (default) | summary | silent
TELEMETRY_MODE = os.getenv("OPSGUARD_TELEMETRY_MODE", "verbose").lower()

# SCHEMA ENFORCEMENT & CONTEXT INJECTION
# Loaded from prompts/system_prompt.txt - edit the file to update prompt behaviour
# without touching Python source code (versioned independently).
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


class AIEngine:
    """Gate 2: semantic security analysis engine powered by an LLM via OpenRouter.

    Sends the git diff to a large language model for contextual reasoning about
    security vulnerabilities that deterministic regex cannot detect (SQL injection,
    logic backdoors, supply-chain typosquatting, etc.).

    Error policy (ADR-0004): fail-closed. Any exception raised during analysis
    returns a BLOCK verdict with risk_score=10 rather than propagating the error.
    This guarantees that no PR passes silently through an engine failure.
    """

    def __init__(self) -> None:
        """Initialise the AI engine and validate the OpenRouter API key.

        Raises:
            AIEngineError: If OPENROUTER_API_KEY is not set in the environment.
        """
        raw_key = os.getenv("OPENROUTER_API_KEY")
        if not raw_key:
            raise AIEngineError("❌ Missing OPENROUTER_API_KEY")

        self.api_key = raw_key.strip().strip('"').strip("'")

        extra_headers = {
            "HTTP-Referer": "https://opsguard.local",
            "X-Title": "OpsGuard-TFM",
        }

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            default_headers=extra_headers,
            timeout=60.0,
        )

        self.model = os.getenv("AI_MODEL")
        if not self.model:
            raise AIEngineError(
                "❌ Missing AI_MODEL — set your preferred model in .env "
                "(e.g. AI_MODEL=google/gemini-2.0-flash-001)"
            )

    def analyze_diff(self, diff_text: str) -> Dict[str, Any]:
        """Analyse a git diff for security vulnerabilities using an LLM.

        Truncates the diff to MAX_DIFF_CHARS before sending it to the model
        to keep cost and latency predictable (ADR-0005).

        Args:
            diff_text: Raw git diff string to analyse.

        Returns:
            A dict with the following keys:
                - ``verdict`` (str): ``"APPROVE"`` or ``"BLOCK"``.
                - ``risk_score`` (int): 0–10. Values ≥ OPSGUARD_RISK_THRESHOLD
                  (default 7) cause the pipeline to block.
                - ``explanation`` (str): Executive summary of the security status.
                - ``findings`` (list): Zero or more dicts, each with keys
                  ``file``, ``line``, ``severity``, and ``issue``.

        Note:
            This method never raises. Any exception (network timeout, malformed
            JSON, unexpected response type) is caught and returns a BLOCK verdict
            with risk_score=10 (fail-closed policy, ADR-0004).
        """
        if TELEMETRY_MODE != "silent":
            _console.print(
                f"🤖 OpsGuard Brain: Sending diff to [cyan]{self.model}[/cyan]..."
            )
        if TELEMETRY_MODE == "verbose":
            _console.print(f"📦 Context Payload: {len(diff_text)} chars")

        start_time = time.time()

        # Defensive truncation - keeps cost and context window predictable.
        original_len = len(diff_text)
        truncated_diff = diff_text[:MAX_DIFF_CHARS]
        if original_len > MAX_DIFF_CHARS and TELEMETRY_MODE != "silent":
            chars_lost = original_len - MAX_DIFF_CHARS
            _console.print(
                f"⚠️  Diff truncated: {original_len} → {MAX_DIFF_CHARS} chars "
                f"({chars_lost} discarded)",
                style="yellow",
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Analyze this git diff:\n\n{truncated_diff}",
                    },
                ],
                temperature=0.1,  # Deterministic: reduces hallucinations
                max_tokens=1024,
                response_format={"type": "json_object"},
            )

            end_time = time.time()
            total_latency_ms = int((end_time - start_time) * 1000)

            if TELEMETRY_MODE == "verbose":
                _console.print(
                    f"⏱️  AI Analysis Time: {total_latency_ms / 1000:.2f}s",
                    style="cyan",
                )

            # --- FINOPS TELEMETRY (ADR-0003) ---
            usage = response.usage
            if usage and TELEMETRY_MODE != "silent":
                input_tok = usage.prompt_tokens
                output_tok = usage.completion_tokens
                input_cost = (input_tok / 1_000_000) * PRICE_PER_1M_INPUT
                output_cost = (output_tok / 1_000_000) * PRICE_PER_1M_OUTPUT
                total_cost = input_cost + output_cost

                table = Table(
                    title="💰 FinOps Telemetry",
                    box=box.MARKDOWN,
                    style="green",
                    title_style="bold green",
                )
                table.add_column("Metric", style="bold")
                table.add_column("Value")
                table.add_column("Unit Cost")
                table.add_row(
                    "Input Tokens", str(input_tok), f"${PRICE_PER_1M_INPUT}/1M"
                )
                table.add_row(
                    "Output Tokens", str(output_tok), f"${PRICE_PER_1M_OUTPUT}/1M"
                )
                table.add_row("Total Latency", f"{total_latency_ms}ms", "N/A")
                # TTFT requires streaming mode; non-streaming total latency ≈ TTFT.
                table.add_row("TTFT (approx)", f"{total_latency_ms}ms", "non-streaming")
                table.add_row("Execution Cost", f"${total_cost:.6f}", "Negligible")
                _console.print(table)
            # ------------------------------------

            content = response.choices[0].message.content
            clean_content = content.replace("```json", "").replace("```", "").strip()

            try:
                parsed_data = json.loads(clean_content)
            except json.JSONDecodeError:
                _console.print(
                    f"⚠️ RAW AI RESPONSE (JSON Error): {clean_content}", style="yellow"
                )
                return {
                    "verdict": "BLOCK",
                    "risk_score": 10,
                    "explanation": "AI output parsing failed. Manual review required.",
                    "findings": [],
                }

            # Normalisation: handle unexpected list responses
            if isinstance(parsed_data, list):
                parsed_data = parsed_data[0] if parsed_data else {}

            return {
                "verdict": parsed_data.get("verdict", "BLOCK"),
                "risk_score": parsed_data.get("risk_score", 0),
                "explanation": parsed_data.get(
                    "explanation", "No explanation provided."
                ),
                "findings": parsed_data.get("findings", []),
            }

        except Exception as e:
            _console.print(f"\n❌ AI Critical Error: {str(e)}", style="bold red")
            # Fail closed: any engine failure blocks the pipeline.
            return {
                "verdict": "BLOCK",
                "risk_score": 10,
                "explanation": f"Internal Engine Error: {str(e)}",
                "findings": [],
            }
