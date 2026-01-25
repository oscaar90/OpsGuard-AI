# OpsGuard-AI

> **Context-Aware Security Gate for GitHub Actions.**
> Validates deployments using Hybrid Analysis (Deterministic Rules + LLM Reasoning).

## Architecture (Day 1 Status)


graph TD
    User[Developer] -->|Push/PR| GH[GitHub Actions]
    GH -->|Trigger| Docker[OpsGuard Container]
    
    subgraph "OpsGuard Runtime"
        CLI[Typer CLI] --> Ingest[Git Context Manager]
        Ingest -->|Check Env| Env{Is CI?}
        Env -- Yes --> JSON[Parse GITHUB_EVENT]
        Env -- No --> Local[Git Diff HEAD]
        JSON & Local --> Diff[Raw Code Delta]
    end
    
    Diff --> Output[Stdout / Report]
