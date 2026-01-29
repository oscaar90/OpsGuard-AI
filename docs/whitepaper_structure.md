# OpsGuard-AI: Technical Whitepaper Structure

## 1. Abstract
Context-aware security gate implementation using Hybrid Analysis (Regex + LLM) to prevent credential leaks and logical vulnerabilities in CI/CD pipelines.

## 2. Problem Statement
- Inefficiency of static linters (high false positives).
- Risk of Low-Code/No-Code tools exporting secrets to version control.
- "Context Blindness" in traditional security tools.

## 3. Architecture (The Hybrid Engine)
- **Phase 1: Deterministic Layer (The Shield).** Local Regex execution. Zero latency. Privacy filter.
- **Phase 2: Semantic Layer (The Brain).** LLM integration via OpenRouter. Intent analysis. JSON structured output.

## 4. Engineering Decisions (ADRs)
- **Language:** Python 3.12 (Native Typing, Ecosystem).
- **Dependency Management:** Poetry (Deterministic builds).
- **CI/CD:** GitHub Actions (Native integration, blocking PRs).

## 5. Security & Privacy Strategy
- **Least Privilege:** CI tokens permissions.
- **Data Minimization:** Sending only `git diff`, not full codebase.
- **Fail-Safe Design:** Pipeline blocks if security scanner fails/crashes.

## 6. Future Work / Roadmap
- Custom Rule Engine via YAML.
- Support for GitLab CI / Azure DevOps.
- Self-hosted LLM support (Ollama).