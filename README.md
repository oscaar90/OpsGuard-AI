<p align="center">
  <strong>🛡️ OpsGuard AI</strong>
  <br/>
  AI security gate for GitHub Actions that blocks vulnerable pull requests before merge.
  <br/>
  <em>Local secret detection first. Semantic AppSec review second.</em>
</p>

<p align="center">
  <a href="https://github.com/oscaar90/OpsGuard-AI/stargazers"><img src="https://img.shields.io/github/stars/oscaar90/OpsGuard-AI?style=social" alt="GitHub stars"/></a>
  <a href="https://github.com/oscaar90/OpsGuard-AI/blob/main/LICENSE"><img src="https://img.shields.io/github/license/oscaar90/OpsGuard-AI" alt="License"/></a>
  <a href="https://github.com/oscaar90/OpsGuard-AI/actions"><img src="https://img.shields.io/github/actions/workflow/status/oscaar90/OpsGuard-AI/ci.yml?label=CI" alt="CI"/></a>
  <a href="https://github.com/oscaar90/OpsGuard-AI/issues"><img src="https://img.shields.io/github/issues/oscaar90/OpsGuard-AI" alt="Issues"/></a>
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/status-stable-brightgreen" alt="Status"/>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README_ES.md">Español</a>
</p>

<p align="center">
  <strong>Built for GitHub PRs</strong> · <strong>Secrets caught locally first</strong> · <strong>~$0.001 per semantic scan</strong> · <strong>Useful against AI-generated insecure code</strong>
</p>

---

## Why People Try OpsGuard

OpsGuard is a two-stage security gate for pull requests:

- **Gate 1** catches hardcoded secrets and known-bad patterns locally in milliseconds.
- **Gate 2** sends the diff to an LLM for contextual review of logic flaws and subtle vulnerabilities.

Traditional scanners mostly match patterns. **OpsGuard also reasons about intent.**

That makes it useful for the kinds of changes that increasingly slip into repos today:

- Hardcoded AWS keys, GitHub tokens, API secrets
- SQL injection and auth bypasses
- Supply-chain typosquatting in deployment code
- Vulnerable code introduced by Copilot, Cursor, Devin, or autonomous coding agents

---

## See It In Action

![OpsGuard blocking a malicious PR](./docs/assets/demo.gif)

Example: a pull request adds a developer backdoor.

```python
def validate_request(headers):
    if headers.get("X-DEBUG-MODE") == "true":
        return True
```

OpsGuard lets Gate 1 pass, sends the diff to Gate 2, and blocks the PR with a semantic finding:

```text
Verdict: BLOCK
Risk Score: 8/10
Issue: Developer backdoor via X-DEBUG-MODE header
```

More examples:

- [Real blocked cases](./docs/ejemplos-reales.md)
- [Benchmark and model comparison](./docs/benchmark-models.md)
- [Fixture inventory / shooting range](./tests/fixtures/README.md)

---

## Why It Stands Out

- **Two-stage architecture**: cheap deterministic checks first, semantic reasoning second.
- **Low-friction adoption**: install it as a GitHub Action in a few lines.
- **Privacy-aware by design**: obvious secrets are caught before any LLM call.
- **Built for the current threat model**: insecure PRs are no longer written only by humans.

This is where OpsGuard is strongest: **security review for code that looks syntactically normal but is operationally dangerous**.

---

## Try It In 2 Minutes

1. Get a free API key at [OpenRouter](https://openrouter.ai).
2. Add it to your repository secrets as `OPENROUTER_API_KEY`.
3. Create `.github/workflows/opsguard.yml`:

```yaml
name: OpsGuard Security Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: oscaar90/OpsGuard-AI@v1
        with:
          openrouter-api-key: ${{ secrets.OPENROUTER_API_KEY }}
```

Every new pull request will go through:

```text
Git Diff -> Gate 1: Local Regex -> Gate 2: LLM Review -> APPROVE / BLOCK
```

---

## What It Catches

### Gate 1: local deterministic detection

- AWS access keys
- GitHub tokens
- Stripe keys
- Generic hardcoded passwords and secrets
- Private keys

Rules live in [`opsguard.yml`](./opsguard.yml).

### Gate 2: semantic analysis

- SQL injection
- Developer backdoors
- Dangerous auth bypasses
- Supply-chain typosquatting
- Insecure AI-generated logic

Examples are documented in [docs/ejemplos-reales.md](./docs/ejemplos-reales.md).

---

## Quick Local Demo

If you want to test it before wiring it into a real repo:

```bash
git clone https://github.com/oscaar90/OpsGuard-AI.git
cd OpsGuard-AI
poetry install
cp .env.example .env
```

Add your `OPENROUTER_API_KEY` to `.env`, then try a fixture:

```bash
cp tests/fixtures/vulnerable_app/legacy_login.py src/legacy_login.py
git add src/legacy_login.py
poetry run opsguard scan
```

Expected result: Gate 1 passes, Gate 2 blocks the SQL injection.

Full local guide:

- [Local setup and testing guide](./docs/guia-local.md)

---

## What Happens When It Blocks

- The GitHub Actions job fails
- The CLI prints a risk score and security explanation
- Findings are shown with file, severity, and issue description
- The PR does not silently pass on LLM failure: OpsGuard is **fail-closed**

Key design choices:

- Gate 1 always runs locally first
- Prompts are kept in English for consistency and token efficiency
- AI errors return `BLOCK`, not `APPROVE`
- Large diffs are truncated to keep latency and cost predictable

See the ADRs in [`docs/adr/`](./docs/adr/).

---

## Who This Is For

- Teams using **GitHub Actions** as their CI gate
- Startups without a dedicated AppSec reviewer
- Teams shipping a lot of **AI-assisted code**
- Repositories that want a lightweight security gate before heavier tooling

OpsGuard is not trying to replace every SAST product. It is trying to be the **fast, cheap, always-on gate** that catches risky pull requests before merge.

---

## Comparison

| Feature | OpsGuard AI | Snyk | SonarQube | Semgrep |
|---------|:-----------:|:----:|:---------:|:-------:|
| LLM semantic analysis | ✅ | ❌ | ❌ | ❌ |
| GitHub Action setup | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Local-first secret gate | ✅ | ✅ | ❌ | ✅ |
| AI-generated code review angle | ✅ | ❌ | ❌ | ❌ |
| Cost-aware per scan | ✅ | ❌ | ❌ | ❌ |

For benchmark methodology and outputs, see [docs/benchmark-models.md](./docs/benchmark-models.md).

---

## Documentation

- [Local setup and testing guide](./docs/guia-local.md)
- [Real blocked examples](./docs/ejemplos-reales.md)
- [Benchmark and model comparison](./docs/benchmark-models.md)
- [Architecture Decision Records](./docs/adr/)
- [Prompt strategy and AI artifacts](./prompts/)
- [Changelog](./CHANGELOG.md)

---

## License

OpsGuard AI uses a **dual license model**:

- **Open Source (AGPLv3)** for personal projects, open-source, and non-production use
- **Commercial License** for closed corporate environments or incompatible copyleft requirements

For commercial licensing: **oscar@oscarsperez.com**

---

<p align="center">
  <em>Built as a Master's Thesis (TFM) — graded <strong>Excellent</strong>.</em>
  <br/>
  <a href="https://github.com/oscaar90/OpsGuard-AI/issues">Issues</a> · <a href="mailto:oscar@oscarsperez.com">Contact</a>
</p>
