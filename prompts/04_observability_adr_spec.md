# Role
Act as a Principal Software Architect.

# Context
We need to document a new architectural decision regarding system observability.
Currently, OpsGuard blocks the pipeline (exit 1), but the logs remain buried in GitHub Actions, making it hard to analyze failure trends (e.g., "Which team introduces the most secrets?").

# Task
Create a new ADR file: `docs/adr/0004-dashboard-observabilidad.md`.

# Output Requirements
1. **Language:** The content MUST be in **Professional Technical Spanish**.
2. **Format:** Standard MADR template.

# Decision Details
* **Title:** Dashboard de Observabilidad y Análisis de Fallos.
* **Context:** Pure CLI logs are insufficient for analyzing security incidents at scale. We need a way to visualize *why* builds are failing without digging into raw console logs.
* **Decision:** Develop an external **Dashboard (Web)** using **Next.js & TypeScript**.
    * **Mechanism:** It will consume the **GitHub Actions API** to retrieve workflow run logs.
    * **AI Layer:** It will use an LLM (via prompt) to parse the failure log and categorize the incident (e.g., "Hardcoded AWS Key", "Generic Error").
    * **Metrics:** It will display security KPIs (Mean Time To Recovery, Blocked Builds %).
* **Consequences:**
    * Requires a GitHub Read-Only Token.
    * Provides data to justify the tool's ROI to stakeholders.

# Output Format
Provide only the raw markdown content for the file `docs/adr/0004-dashboard-observabilidad.md`.