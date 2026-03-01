# OpsGuard-AI - Benchmark de Modelos: Informe Completo

> **Complemento al ADR-0003** · Artefacto de verificación empírica
> Fecha de ejecución: 2026-03-01 · Rama: `main` · Commit: `aad1827`

Este documento recoge los artefactos completos del benchmark documentado en [`docs/adr/0003-telemetria-y-finops.md`](adr/0003-telemetria-y-finops.md). El ADR contiene el resumen ejecutivo y las conclusiones. Este fichero contiene lo que el ADR no incluye por razones de legibilidad: los **registros de telemetría completos por ejecución**, la **justificación textual de cada modelo** y los **casos de aprobación (APPROVE)** que verifican la ausencia de falsos positivos.

---

## Configuración del entorno

```
OPSGUARD_TELEMETRY_MODE=verbose
OPSGUARD_RISK_THRESHOLD=7
OPSGUARD_MODEL=<modelo bajo prueba>
temperature=0.1
max_tokens=1024
timeout=60s
Ejecuciones por combinación: 3 (se registra la mediana de latencia y tokens)
```

Todos los modelos recibieron el mismo system prompt (`prompts/system_prompt.txt`, versión en commit `aad1827`) y el mismo diff en cada fixture. La única variable entre ejecuciones fue el modelo destino de la llamada OpenRouter.

---

## Fixtures del Shooting Range (BLOCK)

### Fixture B1 - `legacy_login.py` (SQL Injection)

**Diff enviado:**
```diff
+import sqlite3
+
+def get_user(username):
+    query = f"SELECT * FROM users WHERE name = '{username}'"
+    conn = sqlite3.connect("db.sqlite")
+    cursor = conn.execute(query)
+    return cursor.fetchone()
```

#### `google/gemini-2.0-flash-001`

```json
{
  "verdict": "BLOCK",
  "risk_score": 9,
  "justification": "The code introduces a critical SQL injection vulnerability. The `username` parameter is interpolated directly into the SQL query string using an f-string without any sanitization or parameterization. An attacker can craft a username such as `' OR '1'='1` to bypass authentication or `'; DROP TABLE users; --` to destroy data. The fix requires replacing the f-string with a parameterized query: `conn.execute('SELECT * FROM users WHERE name = ?', (username,))`.",
  "telemetry": {
    "model": "google/gemini-2.0-flash-001",
    "input_tokens": 1142,
    "output_tokens": 287,
    "ttft_ms": 312,
    "total_latency_ms": 2847,
    "estimated_cost_usd": 0.000228,
    "timestamp": "2026-03-01T09:14:23Z"
  }
}
```

#### `anthropic/claude-haiku-4-5`

```json
{
  "verdict": "BLOCK",
  "risk_score": 10,
  "justification": "This code contains a textbook SQL injection vulnerability. The `username` value is embedded directly into the query string via f-string interpolation (`f\"SELECT * FROM users WHERE name = '{username}'\"`). This allows any attacker with control over the `username` parameter to execute arbitrary SQL. Severity is maximum because the vulnerable query touches authentication logic - a successful injection can grant access to any account, enumerate the database schema, or corrupt data. Must be rewritten using parameterized queries before merge.",
  "telemetry": {
    "model": "anthropic/claude-haiku-4-5",
    "input_tokens": 1142,
    "output_tokens": 312,
    "ttft_ms": 198,
    "total_latency_ms": 1923,
    "estimated_cost_usd": 0.002163,
    "timestamp": "2026-03-01T09:15:01Z"
  }
}
```

#### `openai/gpt-4o-mini`

```json
{
  "verdict": "BLOCK",
  "risk_score": 9,
  "justification": "SQL injection detected. The `get_user` function constructs a SQL query by directly embedding the `username` argument using Python f-string syntax. This pattern is exploitable: a malicious user can inject SQL syntax to manipulate query logic, access unauthorized records, or execute administrative commands on the database. The vulnerable line is `query = f\"SELECT * FROM users WHERE name = '{username}'\"`. Remediation: use parameterized queries `cursor.execute('... WHERE name = ?', (username,))`.",
  "telemetry": {
    "model": "openai/gpt-4o-mini",
    "input_tokens": 1142,
    "output_tokens": 298,
    "ttft_ms": 421,
    "total_latency_ms": 3421,
    "estimated_cost_usd": 0.000351,
    "timestamp": "2026-03-01T09:15:44Z"
  }
}
```

---

### Fixture B2 - `auth_middleware.py` (Developer Backdoor)

**Diff enviado:**
```diff
+import os
+
+def validate_request(headers):
+    api_key = headers.get("X-API-KEY")
+
+    if headers.get("X-DEBUG-MODE") == "true":
+        return True  # Bypass auth completely
+
+    if not api_key:
+        return False
+
+    return api_key == os.getenv("SERVICE_SECRET")
```

#### `google/gemini-2.0-flash-001`

```json
{
  "verdict": "BLOCK",
  "risk_score": 8,
  "justification": "The function contains an intentional authentication bypass. The condition `if headers.get('X-DEBUG-MODE') == 'true': return True` allows any caller who sends the `X-DEBUG-MODE: true` header to skip all authentication checks unconditionally. This is the classic developer backdoor pattern: created for local debugging convenience but committed to the codebase and deployable to production. Any service that consumes this middleware becomes fully unauthenticated for anyone who knows the header name. Remove the backdoor block before merge.",
  "telemetry": {
    "model": "google/gemini-2.0-flash-001",
    "input_tokens": 1287,
    "output_tokens": 341,
    "ttft_ms": 287,
    "total_latency_ms": 3102,
    "estimated_cost_usd": 0.000265,
    "timestamp": "2026-03-01T09:21:17Z"
  }
}
```

#### `anthropic/claude-haiku-4-5`

```json
{
  "verdict": "BLOCK",
  "risk_score": 9,
  "justification": "Developer backdoor detected in authentication middleware. The `X-DEBUG-MODE` header check at line 8 provides a complete authentication bypass: when this header is present with value `true`, the function returns `True` immediately without validating any credential. This pattern is especially dangerous because the bypass is disguised as a debugging facility - the comment `# Bypass auth completely` in the diff even documents the intent. In production, any client with knowledge of this header can impersonate any user or service. The fix is simple: remove the backdoor block entirely. Debug-mode behavior belongs in test doubles, not in production middleware.",
  "telemetry": {
    "model": "anthropic/claude-haiku-4-5",
    "input_tokens": 1287,
    "output_tokens": 356,
    "ttft_ms": 203,
    "total_latency_ms": 2187,
    "estimated_cost_usd": 0.002452,
    "timestamp": "2026-03-01T09:21:58Z"
  }
}
```

#### `openai/gpt-4o-mini`

```json
{
  "verdict": "BLOCK",
  "risk_score": 8,
  "justification": "Authentication backdoor identified. The `validate_request` function includes a debug bypass: if the `X-DEBUG-MODE` header equals `'true'`, authentication is skipped entirely and the function returns `True`. This effectively creates an unauthenticated access path for anyone who knows the header. The commented explanation `# Bypass auth completely` confirms this is intentional, which makes the risk higher - it suggests awareness of the security impact. This must not be merged into any environment. Remove lines 7-8 before approval.",
  "telemetry": {
    "model": "openai/gpt-4o-mini",
    "input_tokens": 1287,
    "output_tokens": 334,
    "ttft_ms": 398,
    "total_latency_ms": 3891,
    "estimated_cost_usd": 0.000393,
    "timestamp": "2026-03-01T09:22:41Z"
  }
}
```

---

### Fixture B3 - `config.php` (Hardcoded Secrets)

**Diff enviado:**
```diff
+<?php
+return [
+    'debug' => true,
+    'database' => [
+        'host' => 'localhost',
+        'password' => 'admin1234',
+    ],
+    'openai' => [
+        'api_key' => 'sk-proj-1234567890abcdef1234567890abcdef',
+    ]
+];
```

| Modelo | Veredicto | Risk | Latencia | Tokens in/out | Coste |
|--------|:---------:|:----:|:--------:|:-------------:|:-----:|
| `google/gemini-2.0-flash-001` | BLOCK | 10/10 | 1 987 ms | 987 / 256 | $0.000201 |
| `anthropic/claude-haiku-4-5` | BLOCK | 10/10 | 1 654 ms | 987 / 278 | $0.001903 |
| `openai/gpt-4o-mini` | BLOCK | 10/10 | 2 678 ms | 987 / 267 | $0.000309 |

> Los tres modelos convergieron en `risk_score=10` de forma unánime. La justificación común: el diff expone simultáneamente dos tipos de secretos hardcodeados (`database.password` en plaintext y un API key de OpenAI en formato `sk-proj-*`) más `debug=true` activo. Cualquiera de los tres sería suficiente para bloquear; la combinación eleva la puntuación al máximo.

---

### Fixture B4 - `supply_chain_attack.py` (Typosquatting `ghrc.io`)

**Diff enviado:**
```diff
+REGISTRY = (
+    "ghrc.io"  # Should be ghcr.io (GitHub Container Registry)
+)
+
+def build_and_push(tag: str = "latest"):
+    full_image = f"{REGISTRY}/{ORG}/{IMAGE_NAME}:{tag}"
+    subprocess.run(["docker", "build", "-t", full_image, "."], check=True)
+    subprocess.run(["docker", "push", full_image], check=True)
```

> Este fixture es el **caso de prueba más exigente del benchmark**. El dominio `ghrc.io` es sintácticamente válido, no contiene ningún patrón léxico reconocible como malicioso y la diferencia con `ghcr.io` (registro oficial de GitHub) es un único carácter transpuesto. Solo el razonamiento contextual - entender que este código es un pipeline de CI/CD que empuja imágenes a producción, y que `ghrc.io` no es un dominio legítimo conocido - permite identificar el riesgo.

#### `google/gemini-2.0-flash-001`

```json
{
  "verdict": "BLOCK",
  "risk_score": 7,
  "justification": "Potential typosquatting attack detected in container registry configuration. The `REGISTRY` constant is set to `ghrc.io`, which appears to be a typosquatted version of `ghcr.io` (GitHub Container Registry). The difference is a single character transposition (`ghrc` vs `ghcr`). In a CI/CD pipeline that builds and pushes production Docker images, this would cause images to be pushed to an attacker-controlled registry instead of the legitimate GitHub registry. Any downstream system pulling from `ghrc.io` would receive potentially malicious images. Verify the intended registry URL before merging.",
  "telemetry": {
    "model": "google/gemini-2.0-flash-001",
    "input_tokens": 1143,
    "output_tokens": 398,
    "ttft_ms": 334,
    "total_latency_ms": 3456,
    "estimated_cost_usd": 0.000274,
    "timestamp": "2026-03-01T09:31:09Z"
  }
}
```

#### `anthropic/claude-haiku-4-5`

```json
{
  "verdict": "BLOCK",
  "risk_score": 8,
  "justification": "Supply chain attack via registry typosquatting. The constant `REGISTRY = 'ghrc.io'` contains a single-character transposition of the legitimate GitHub Container Registry domain `ghcr.io`. This is a known typosquatting attack vector: by controlling `ghrc.io`, an attacker can serve malicious container images to any pipeline that uses this configuration. The impact is severe because this code calls `docker push` - it would upload production images to the attacker-controlled registry - and any downstream consumer calling `docker pull` from `ghrc.io` would receive a compromised image. The same typo appears twice in the file (REGISTRY constant and pull_base_image function), suggesting this was introduced intentionally rather than as a typo.",
  "telemetry": {
    "model": "anthropic/claude-haiku-4-5",
    "input_tokens": 1143,
    "output_tokens": 421,
    "ttft_ms": 211,
    "total_latency_ms": 2341,
    "estimated_cost_usd": 0.002599,
    "timestamp": "2026-03-01T09:31:52Z"
  }
}
```

#### `openai/gpt-4o-mini`

```json
{
  "verdict": "BLOCK",
  "risk_score": 7,
  "justification": "Suspicious container registry domain detected. `ghrc.io` does not match the official GitHub Container Registry hostname `ghcr.io`. The single-character difference (`ghrc` vs `ghcr`) is characteristic of a typosquatting domain. This pipeline pushes production Docker images to this registry and also pulls base images from it - both operations would interact with the potentially malicious domain. Recommend verifying whether `ghrc.io` is an intentional private registry or a typo before merging. If it is a typo, replace with `ghcr.io`.",
  "telemetry": {
    "model": "openai/gpt-4o-mini",
    "input_tokens": 1143,
    "output_tokens": 387,
    "ttft_ms": 412,
    "total_latency_ms": 4123,
    "estimated_cost_usd": 0.000404,
    "timestamp": "2026-03-01T09:32:38Z"
  }
}
```

---

## Fixtures de Aprobación (APPROVE)

> Verificación de ausencia de falsos positivos. Un sistema de seguridad sobreconservador que bloquea código legítimo es tan inútil como uno que no detecta amenazas - genera fatiga de alertas y lleva a los equipos a desactivar la herramienta.

### Fixture A1 - `clean_query.py` (versión segura de B1)

El mismo módulo de consulta a base de datos de Fixture B1, reescrito correctamente.

**Diff enviado:**
```diff
+import sqlite3
+from typing import Optional
+
+def get_user(username: str) -> Optional[dict]:
+    """Retrieve user by username using a parameterized query."""
+    query = "SELECT id, name, email FROM users WHERE name = ?"
+    with sqlite3.connect("db.sqlite") as conn:
+        cursor = conn.execute(query, (username,))
+        row = cursor.fetchone()
+        if row:
+            return {"id": row[0], "name": row[1], "email": row[2]}
+    return None
```

| Modelo | Veredicto | Risk | Latencia | Justificación resumida |
|--------|:---------:|:----:|:--------:|------------------------|
| `google/gemini-2.0-flash-001` | ✅ APPROVE | 1/10 | 1 823 ms | Parameterized query - no injection vector |
| `anthropic/claude-haiku-4-5` | ✅ APPROVE | 1/10 | 1 412 ms | Safe database access pattern, context manager, typed signature |
| `openai/gpt-4o-mini` | ✅ APPROVE | 2/10 | 2 341 ms | No security concerns - uses `?` placeholder correctly |

#### `google/gemini-2.0-flash-001` (respuesta completa)

```json
{
  "verdict": "APPROVE",
  "risk_score": 1,
  "justification": "This is a secure database query implementation. The SQL query uses a parameterized placeholder (`?`) and passes the username as a separate tuple argument to `conn.execute()`. This pattern completely eliminates the SQL injection risk - the database driver handles escaping and type coercion. The use of a context manager (`with sqlite3.connect`) ensures the connection is closed properly. The typed signature and Optional return type indicate defensive coding practices. No security concerns.",
  "telemetry": {
    "model": "google/gemini-2.0-flash-001",
    "input_tokens": 1198,
    "output_tokens": 198,
    "ttft_ms": 267,
    "total_latency_ms": 1823,
    "estimated_cost_usd": 0.000187,
    "timestamp": "2026-03-01T09:41:12Z"
  }
}
```

---

### Fixture A2 - `clean_refactor.py` (refactoring sin cambios de seguridad)

Caso de uso cotidiano: un PR que solo reorganiza código sin tocar ninguna superficie de ataque.

**Diff enviado:**
```diff
-def process_items(items):
-    result = []
-    for item in items:
-        if item > 0:
-            result.append(item * 2)
-    return result
+def process_items(items: list[int]) -> list[int]:
+    """Return doubled values for all positive integers in the input list."""
+    return [item * 2 for item in items if item > 0]
```

| Modelo | Veredicto | Risk | Latencia | Justificación resumida |
|--------|:---------:|:----:|:--------:|------------------------|
| `google/gemini-2.0-flash-001` | ✅ APPROVE | 0/10 | 1 234 ms | Pure refactor - no security surface |
| `anthropic/claude-haiku-4-5` | ✅ APPROVE | 0/10 | 1 098 ms | Equivalent logic, improved readability, no security impact |
| `openai/gpt-4o-mini` | ✅ APPROVE | 0/10 | 1 876 ms | Style-only change, no security concern |

> Los tres modelos devolvieron `risk_score=0` - el mínimo posible - para este diff. Esto confirma que el sistema no produce falsos positivos ante refactorings rutinarios: no hay penalización por mejorar código legítimo.

---

### Fixture A3 - `pathspec_usage.py` (falso positivo detectado en dog-fooding)

> **Contexto:** Durante el dog-fooding de OpsGuard sobre su propio repositorio, Gate 2 generó un falso positivo al analizar un diff que importaba la librería `pathspec`. El modelo interpretó "bypass" (presente en el nombre de un método interno de `pathspec`) como un intento de eludir controles de seguridad. Este fixture documenta el caso real y verifica que la CRITICAL CONTEXTUAL RULE añadida al system prompt lo resuelve.

**Diff enviado:**
```diff
+import pathspec
+
+def load_ignore_patterns(ignore_file: str) -> pathspec.PathSpec:
+    """Load .opsguardignore patterns for file filtering."""
+    with open(ignore_file) as f:
+        patterns = f.read().splitlines()
+    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
+
+def should_ignore(path: str, spec: pathspec.PathSpec) -> bool:
+    """Return True if the path matches any ignore pattern."""
+    return spec.match_file(path)
```

| Modelo | Veredicto | Risk | Latencia | Resultado |
|--------|:---------:|:----:|:--------:|-----------|
| `google/gemini-2.0-flash-001` | ✅ APPROVE | 1/10 | 1 654 ms | Correcto - librería legítima reconocida |
| `anthropic/claude-haiku-4-5` | ✅ APPROVE | 0/10 | 1 287 ms | Correcto - pattern matching estándar |
| `openai/gpt-4o-mini` | ✅ APPROVE | 1/10 | 2 109 ms | Correcto - `.opsguardignore` interpretado como mecanismo de filtrado, no de evasión |

> **Verificación de la CRITICAL CONTEXTUAL RULE:** La regla añadida al system prompt ("Importing a library named `pathspec` to implement file ignore patterns is NOT a security bypass - it is standard .gitignore-style filtering") resolvió el falso positivo en los tres modelos. Documentado en `prompts/README.md`.

---

## Resumen estadístico completo

### Matriz de resultados (7 fixtures × 3 modelos = 21 ejecuciones)

| Fixture | Tipo | Gate | Gemini Flash | Claude Haiku | GPT-4o-mini |
|---------|------|:----:|:------------:|:------------:|:-----------:|
| B1 `legacy_login.py` | SQL Injection | 2 | BLOCK (9) | BLOCK (10) | BLOCK (9) |
| B2 `auth_middleware.py` | Backdoor | 2 | BLOCK (8) | BLOCK (9) | BLOCK (8) |
| B3 `config.php` | Hardcoded Secrets | 2 | BLOCK (10) | BLOCK (10) | BLOCK (10) |
| B4 `supply_chain_attack.py` | Typosquatting | 2 | BLOCK (7) | BLOCK (8) | BLOCK (7) |
| A1 `clean_query.py` | Safe code | - | APPROVE (1) | APPROVE (1) | APPROVE (2) |
| A2 `clean_refactor.py` | Refactor | - | APPROVE (0) | APPROVE (0) | APPROVE (0) |
| A3 `pathspec_usage.py` | False positive | - | APPROVE (1) | APPROVE (0) | APPROVE (1) |

### Métricas por modelo

| Métrica | Gemini Flash 2.0 | Claude Haiku 4.5 | GPT-4o-mini |
|---------|:----------------:|:----------------:|:-----------:|
| Verdaderos positivos (4/4 BLOCK) | 4/4 ✅ | 4/4 ✅ | 4/4 ✅ |
| Falsos positivos (0/3 APPROVE) | 0/3 ✅ | 0/3 ✅ | 0/3 ✅ |
| Precisión total (7/7) | 7/7 ✅ | 7/7 ✅ | 7/7 ✅ |
| Latencia media (ms) | **2 848** | **2 026** | **3 528** |
| Coste medio por análisis (USD) | **$0.000242** | **$0.002279** | **$0.000364** |
| Coste mensual estimado (1 000 PRs) | **$0.24** | **$2.28** | **$0.36** |

### Perfil de latencia por fixture (mediana de 3 ejecuciones, ms)

```
Fixture              Gemini Flash    Claude Haiku    GPT-4o-mini
─────────────────────────────────────────────────────────────────
B1 SQL Injection          2 847          1 923          3 421
B2 Backdoor               3 102          2 187          3 891
B3 Hardcoded Secrets      1 987          1 654          2 678
B4 Typosquatting          3 456          2 341          4 123
A1 Clean query            1 823          1 412          2 341
A2 Clean refactor         1 234          1 098          1 876
A3 Pathspec               1 654          1 287          2 109
─────────────────────────────────────────────────────────────────
Media                     2 300          1 700          2 920
```

> La latencia de Claude Haiku es consistentemente la más baja en todos los fixtures. La ventaja es real pero no determinante: la diferencia práctica entre 1 700 ms y 2 300 ms en el contexto de un pipeline de CI/CD que ya tarda minutos en ejecutar lint + tests es despreciable para el desarrollador. El coste, en cambio, es 9.5× mayor.

---

## Análisis del fixture más exigente: Typosquatting (B4)

El fixture `supply_chain_attack.py` merece análisis adicional porque es cualitativamente diferente al resto.

**¿Por qué es más difícil?**

| Propiedad | B1-B3 | B4 |
|-----------|-------|----|
| Patrón léxico reconocible | Sí (`f"SELECT..."`, `X-DEBUG-MODE`, `sk-proj-*`) | No |
| Requiere conocimiento de dominio externo | No | Sí (`ghcr.io` es el dominio legítimo) |
| Requiere razonamiento sobre consecuencias | Parcial | Completo (empuja imágenes a producción) |
| Risk score medio obtenido | 9.3/10 | 7.3/10 |

Los tres modelos detectaron el ataque, pero con `risk_score` más bajo (7-8 vs 9-10 en los otros fixtures). Esto es **comportamiento correcto**: el sistema expresa incertidumbre apropiada ante un caso de razonamiento contextual puro, mientras sigue superando el threshold de bloqueo (`≥ 7`). Un sistema que devuelve `10/10` para todos los casos indiscriminadamente no tiene calibración real.

---

## Modelo seleccionado: `google/gemini-2.0-flash-001`

### Rationale cuantitativo

```
Precisión de detección:  Gemini = Claude = GPT   (empate)
Falsos positivos:        Gemini = Claude = GPT   (empate - todos 0/3)
Latencia:                Claude > Gemini > GPT   (Claude gana por 600 ms)
Coste:                   Gemini > GPT > Claude   (Gemini gana por 9.5×)

Decisión: Gemini Flash.
La latencia de Claude no justifica un coste 9.5× superior.
```

### Proyección de coste a escala

| Escala (PRs/mes) | Gemini Flash | Claude Haiku | Diferencia anual |
|:----------------:|:------------:|:------------:|:----------------:|
| 500 | $0.12 | $1.14 | $12.24 |
| 1 000 | $0.24 | $2.28 | $24.48 |
| 5 000 | $1.20 | $11.40 | $122.40 |
| 10 000 | $2.40 | $22.80 | $244.80 |

> A 10 000 PRs/mes (escala de un equipo de 50-100 ingenieros activos), Gemini Flash cuesta **$244.80/año** frente a los **$2 745.60/año** de Claude Haiku. La herramienta se paga sola en la primera semana de ahorro en una brecha de seguridad que detecta.

---

## Reproducibilidad

Cualquier evaluador puede reproducir este benchmark ejecutando OpsGuard en modo local contra los fixtures del Shooting Range:

```bash
git clone https://github.com/oscaar90/OpsGuard-AI.git
cd OpsGuard-AI
poetry install
export OPENROUTER_API_KEY=<tu_api_key>

# Ejemplo: reproducir Fixture B1 con Gemini Flash
git diff HEAD~1 -- tests/fixtures/vulnerable_app/legacy_login.py | \
  OPSGUARD_MODEL=google/gemini-2.0-flash-001 \
  OPSGUARD_TELEMETRY_MODE=verbose \
  poetry run opsguard scan
```

Los fixtures del Shooting Range están documentados en [`tests/fixtures/README.md`](../tests/fixtures/README.md).

---

*Documento generado como artefacto de verificación del benchmark documentado en ADR-0003.*
*OpsGuard-AI v1.0.2 · Commit `aad1827` · Marzo 2026*
