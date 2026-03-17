# Directorio `prompts/`

Este directorio contiene dos tipos de artefactos de prompt engineering con propósitos distintos:

| Fichero | Tipo | Propósito |
|---------|------|-----------|
| `system_prompt.txt` | **Prompt de producción** | System prompt que Gate 2 envía al LLM en cada análisis |
| `01_git_ingest_spec.md` … `06_web_dashboard.md` | **Prompts de desarrollo** | Especificaciones usadas para construir el proyecto con IA |

---

## 1. `system_prompt.txt` - El prompt de producción de Gate 2

Este fichero es la "inteligencia" de Gate 2. Se carga en tiempo de importación desde `src/ai.py` y se envía como `system` message en cada llamada a la API del LLM (ADR-0002, ADR-0005).

### Anatomía del prompt

```
ROLE → CONTEXT → TASK → CRITICAL CONTEXTUAL RULES → OUTPUT FORMAT
```

#### ROLE y CONTEXT: establecer la autoridad

```
ROLE: You are OpsGuard-AI, a Senior Application Security Engineer audit bot.
CONTEXT: You are auditing the source code of "OpsGuard", a DevSecOps CLI tool.
```

Asignar un rol experto concreto ("Senior Application Security Engineer") en lugar de un rol genérico ("security assistant") mejora la precisión de las respuestas. El CONTEXT fija el dominio del problema: el modelo sabe que está analizando un tool de seguridad, no una aplicación web, un sistema de pagos o una app móvil.

#### CRITICAL CONTEXTUAL RULES: el aprendizaje más importante

Estas reglas son el resultado de iterar sobre el prompt después de observar falsos positivos reales. La más crítica:

> *"Code that implements file filtering (e.g., parsing `.opsguardignore`, using `pathspec`), git operations, or config loading is INTENDED FUNCTIONALITY. Do NOT flag this as a 'Security Bypass' or 'Malicious Filtering'."*

**Problema detectado:** En las primeras versiones del prompt, cuando OpsGuard analizaba sus propios PRs (dog-fooding), el LLM flagueaba el código de `ingest.py` que filtra ficheros mediante `pathspec` como un posible "bypass de seguridad". Esto era un falso positivo crítico: bloquear los PRs del propio proyecto por código legítimo.

**Solución:** Reglas contextuales explícitas que anclan al modelo en el dominio correcto. El LLM necesita saber que lo que parece "filtrar ficheros" en un contexto malicioso es exactamente lo que debe hacer un security gate.

La regla 2 (rutas de fichero ≠ PII) surgió del mismo proceso: `get_staged_files()` listaba rutas de fichero que el modelo marcaba como "data leak". La regla lo previene explícitamente.

#### OUTPUT FORMAT: contrato de schema estricto

```json
{
    "verdict": "APPROVE" | "BLOCK",
    "risk_score": <integer 0-10>,
    "explanation": "...",
    "findings": [...]
}
```

El schema JSON se incluye en el propio prompt - no se delega al parámetro `response_format` del SDK exclusivamente. Esta redundancia es intencional: diferentes modelos del ecosistema OpenRouter respetan el `response_format` con distinta fidelidad. El schema en el prompt actúa como fallback.

El campo `risk_score` (entero 0–10) permite gradación de riesgo en lugar de un veredicto binario. Esto habilita el threshold configurable (`OPSGUARD_RISK_THRESHOLD`, por defecto 7) sin cambiar el prompt.

### Decisiones de prompt engineering

| Decisión | Elección | Alternativa descartada | Razón |
|----------|----------|----------------------|-------|
| Idioma | Inglés | Español | ADR-0002: ~15% menos tokens, modelos optimizados para inglés |
| Temperatura | `0.1` (en código) | `0.0` o `0.5` | Próximo a determinista pero con margen para variación contextual |
| Rol | "Senior AppSec Engineer audit bot" | "security assistant" | Rol experto reduce hallucinations genéricas |
| Schema | Incluido en prompt + `response_format` | Solo `response_format` | Redundancia para compatibilidad con distintos modelos via OpenRouter |
| Reglas contextuales | Explícitas y numeradas | Implícitas en el rol | La especificidad elimina clases enteras de falsos positivos |

### Evolución del prompt

| Versión | Cambio | Motivación |
|---------|--------|------------|
| v1 (inicial) | Prompt minimalista: rol + tarea + schema | Primera integración con Gemini 1.5 Flash |
| v2 | Añade `CRITICAL CONTEXTUAL RULES 1 y 2` | Falsos positivos detectados en dog-fooding (OpsGuard analizando sus propios PRs) |
| v3 (actual) | Externalización a `system_prompt.txt` | ADR-0005: separar artefacto de configuración del código Python |

---

## 2. Prompts de desarrollo (01–06) - Flujo de Desarrollo con IA

Estos ficheros documentan el proceso de construcción del proyecto usando IA como herramienta de ingeniería. Cada prompt es una especificación técnica estructurada que se proporcionó a un LLM para implementar un módulo del sistema.

Este artefacto materializa el módulo **"Flujo de Desarrollo con IA"** del plan de estudios del Máster: no solo se construyó un sistema que usa IA, sino que la IA fue parte integral del proceso de construcción.

### Inventario

| Fichero | Rol asignado al LLM | Módulo construido |
|---------|--------------------|--------------------|
| `01_git_ingest_spec.md` | Senior Python DevOps Engineer | `src/ingest.py` - `GitManager` (lectura de diffs en local y CI) |
| `02_create_adrs.md` | Principal Software Architect | `docs/adr/0001`, `0002`, `0003` - decisiones arquitectónicas iniciales |
| `03_policy_engine_spec.md` | Senior Security Engineer | `src/security.py` - Gate 1 Regex engine + `opsguard.yml` |
| `04_observability_adr_spec.md` | Principal Software Architect | Observabilidad y telemetría FinOps |
| `05_ai_integration.md` | Principal AI Engineer | `src/ai.py` - Gate 2 AI engine (integración LLM) |
| `06_web_dashboard.md` | Senior Frontend Engineer | `web/` - dashboard de monitorización (Next.js / Vercel) |

### Patrón de los prompts de desarrollo

Cada prompt sigue la misma estructura:

```
# Role      → Perfil experto que el LLM debe adoptar
# Context   → Estado actual del proyecto y dependencias previas
# Task N    → Tarea atómica y bien acotada
# Output    → Formato exacto de la respuesta esperada
```

Esta estructura garantiza que cada respuesta del LLM sea:
- **Reproducible**: el mismo prompt produce resultados equivalentes
- **Integrable**: el output encaja directamente en la estructura del proyecto
- **Auditable**: cada decisión de diseño tiene su prompt como artefacto de trazabilidad

### Relación entre prompts y ADRs

Los prompts de desarrollo y los ADRs son artefactos complementarios del mismo proceso de toma de decisiones:

- El prompt `02_create_adrs.md` define las tres decisiones arquitectónicas fundamentales (Gatekeeper local, inglés en prompts, telemetría FinOps)
- Los ADRs resultantes documentan esas decisiones para el equipo
- El `system_prompt.txt` implementa la decisión del ADR-0002 (inglés) y es a su vez el artefacto central que los ADRs documentan
