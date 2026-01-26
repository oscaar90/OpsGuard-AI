# Role
Act as a Principal Software Architect for a critical University Master's Project (TFM).

# Task
We need to document critical architectural decisions using the **ADR (Architecture Decision Record)** format.
Create three markdown files in the `docs/adr/` folder.

# Output Requirements
1. **Language:** The content of the ADR files MUST be written in **Professional Technical Spanish**.
2. **Format:** Use the standard MADR template (Title, Status, Context, Decision, Consequences).
3. **Tone:** Formal, concise, and engineering-focused.

# Input Data

## Decision 1: The Local Gatekeeper Pattern
* **Context:** We are building a GitHub Action that uses LLMs to detect security issues. However, sending code with potential secrets (API keys, passwords) to an external LLM API constitutes a data leak itself.
* **Decision:** We will implement a "Local Gatekeeper" layer using Regex and deterministic rules *before* any data leaves the container. If a hard secret is detected locally, the pipeline fails immediately (Hard Fail). The LLM is never contacted with raw secrets.
* **Status:** Accepted.

## Decision 2: English-First Prompt Engineering
* **Context:** The project uses LLMs (Claude/Gemini) for reasoning. Using Spanish prompts increases token consumption (higher cost/latency) and slightly increases the risk of "hallucinations" or misinterpretations by the model, as they are optimized for English.
* **Decision:** All system prompts sent to the LLM will be in **Technical English**. However, user-facing documentation (ADRs, Readme) will remain in Spanish for the University Tribunal.
* **Status:** Accepted.

## Decision 3: FinOps & Observability Strategy
* **Context:** LLM inference costs and latency are critical factors for CI/CD pipelines. A slow or expensive check will be rejected by engineering teams. We need empirical data to choose the right model (e.g., Gemini Flash vs Claude Sonnet).
* **Decision:** The system will implement a "Verbose Telemetry Mode" by default. It will log strict metrics for every interaction: Input Tokens, Output Tokens, Time-To-First-Token (TTFT), and Total Latency. This data will be used to calculate the "Cost per Run" and justify the model selection in the final thesis.
* **Status:** Accepted.

# Output Format
Generate the full content for:
1. `docs/adr/0001-patron-gatekeeper-local.md`
2. `docs/adr/0002-prompting-en-ingles.md`
3. `docs/adr/0003-telemetria-y-finops.md`
