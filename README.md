# 🛡️ OpsGuard AI

> **Stop a leaked secret from destroying your production environment — before the damage is done.**

![Python](https://img.shields.io/badge/python-3.12-blue)
![Status](https://img.shields.io/badge/status-stable-green)
![CI/CD](https://img.shields.io/badge/github--actions-enabled-brightgreen)
![License](https://img.shields.io/badge/license-AGPL--v3-blue)

---

## The Problem

Every week, developers accidentally push passwords, API keys, and database credentials to GitHub.

Sometimes it's a `.env` file committed by mistake. Sometimes it's a hardcoded token left in a test. Sometimes it's a subtle SQL injection hiding inside what looks like normal code.

The consequences are real: **stolen data, compromised infrastructure, six-figure cloud bills, and public incidents that end careers.**

Traditional security tools help — but they either miss the subtle ones, or they cry wolf so often that developers start ignoring the alerts.

**OpsGuard was built to fix that.**

---

## What OpsGuard Does

OpsGuard sits inside your development pipeline and acts as a **security checkpoint**: every time a developer tries to push code, OpsGuard reviews it automatically.

Think of it as a bouncer at the door. Fast, smart, and hard to fool.

It works in two stages:

1. **Speed check** — A rule-based engine instantly scans for known dangerous patterns: API keys, passwords, tokens, suspicious credentials. If it finds one, it blocks the push immediately.

2. **Intelligence check** — If nothing obvious is found, an AI reads the code and *understands what it does*. It can detect things no rule can catch — like a login function that bypasses authentication, or a database query that can be manipulated by an attacker.

Only code that passes both gates reaches production.

---

## What It Catches

| Type | Example | Detection |
|------|---------|-----------|
| AWS credentials | `AKIA...` keys in any file | ❌ Blocked instantly |
| Database passwords | Hardcoded `db_password = "..."` | ❌ Blocked instantly |
| SQL Injection | Login logic vulnerable to `' OR 1=1` | ❌ Blocked by AI |
| Logic backdoors | Auth checks that can be bypassed | ❌ Blocked by AI |
| Clean code | Normal application logic | ✅ Approved |
| Documentation | Comments, README files | ✅ Approved |

---

## See It In Action

Run OpsGuard against the included test suite of intentionally vulnerable files:

```bash
poetry run opsguard scan --path tests/fixtures/vulnerable_app
```

**Gate 1 — Regex Engine:** An AWS key is detected and the pipeline is blocked instantly, before any AI call is made.

![Regex engine blocking an AWS Access Key](<docs/evidence/bloqueo local.png>)

**Gate 2 — AI Semantic Analysis:** No obvious pattern found, but the AI reads the logic and identifies a SQL Injection and a hardcoded backdoor. Risk Score: 9/10.

![AI semantic analysis detecting SQL Injection and logic backdoor](<docs/evidence/Deteccion vulnerabilidades logicas.png>)

Real execution logs and screenshots are available in [`/docs/evidence`](/docs/evidence).

---

## Get Started

**Requirements:** Python 3.12+ and [Poetry](https://python-poetry.org/docs/)

```bash
# 1. Clone the repository
git clone https://github.com/oscaar90/OpsGuard-AI.git
cd OpsGuard-AI

# 2. Install dependencies
poetry install

# 3. Add your API key
cp .env.example .env
# Open .env and paste your OPENROUTER_API_KEY
```

That's it. Run the scan command above and see it work.

> **Where do I get an API key?**
> OpsGuard uses [OpenRouter](https://openrouter.ai/) as the AI gateway. Create a free account, generate a key, and set it in your `.env`:
> ```
> OPENROUTER_API_KEY=your_key_here
> AI_MODEL=your_preferred_model
> ```
> OpenRouter gives you access to hundreds of models — Gemini, GPT-4, Claude, Mistral, and more. Use whichever fits your needs or budget.

---

## How It Fits Into Your Workflow

OpsGuard is designed to run automatically — you don't have to remember to use it.

```mermaid
graph TD
    User[Developer] -->|Git Push / Pull Request| CLI[OpsGuard CLI]

    subgraph "Hybrid Analysis Engine"
        CLI -->|Step 1: Static Analysis| Regex[Regex Engine]
        Regex -->|Match found?| Gate1{Sensitive Pattern?}

        Gate1 -- Yes --> Block["❌ BLOCK PIPELINE"]
        Gate1 -- No --> AI["Step 2: AI Semantic Analysis"]

        AI -->|Contextual Reasoning| Gate2{Risk Score > 7?}
        Gate2 -- Yes --> Block
        Gate2 -- No --> Pass["✅ APPROVE DEPLOY"]
    end

    Block & Pass --> Report["CI/CD Report (Console / GitHub Actions)"]
```

For production use, OpsGuard runs automatically via GitHub Actions on every push and pull request. No manual steps needed.

Configuration: `.github/workflows/opsguard.yml`
Required secret: `OPENROUTER_API_KEY` → set it once in your repository settings.

---

## For the Technical Reader

If you want to go deeper into the architecture, the reasoning behind every design decision is documented in the **Architecture Decision Records (ADR)**:

- [ADR-001: Local Gatekeeper Pattern](/docs/adr/0001-patron-gatekeeper-local.md)
- [ADR-002: Prompt Engineering in English](/docs/adr/0002-prompting-en-ingles.md)
- [ADR-003: Telemetry & FinOps](/docs/adr/0003-telemetria-y-finops.md)

**Tech stack:** Python 3.12 · Poetry · OpenRouter (model-agnostic) · Typer · Rich · GitHub Actions · Pytest

---

## Contributing

This project follows **[Conventional Commits](https://www.conventionalcommits.org/)**.

| Type | Use for |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `chore` | Maintenance / config |
| `test` | Tests |

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

You are free to use, study, modify, and distribute this software — as long as any derivative work is also released under the same license. If you use OpsGuard as part of a network service, you must also make your modifications publicly available.

**In short:** use it freely, improve it openly, but you cannot take it and close it.

For commercial licensing or partnership inquiries: contacto@oscarsp.dev

See the [LICENSE](LICENSE) file for full terms.

---

---

**Built by [Óscar Sánchez Pérez](https://github.com/oscaar90)**

If OpsGuard saved your pipeline — or you just think the idea is solid — give it a ⭐ and share it. The project is actively evolving and contributions are welcome.
