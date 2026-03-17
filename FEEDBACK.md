# FEEDBACK.md - Análisis Técnico del Proyecto OpsGuard-AI

> Documento de revisión interna generado para identificar áreas de mejora antes de la defensa del TFM.
> Alcance: análisis estático del código fuente, configuración, tests, documentación y coherencia arquitectónica.

---

## Índice

1. [Bug Crítico Activo (Blocker)](#1-bug-crítico-activo-blocker)
2. [Cobertura de Tests - Ausencia de Tests Unitarios Reales](#2-cobertura-de-tests--ausencia-de-tests-unitarios-reales)
3. [Inconsistencias entre Configuración y Código](#3-inconsistencias-entre-configuración-y-código)
4. [Brechas entre ADRs y la Implementación Real](#4-brechas-entre-adrs-y-la-implementación-real)
5. [Calidad del Código - Deuda Técnica Menor](#5-calidad-del-código--deuda-técnica-menor)
6. [Dependencias no Declaradas](#6-dependencias-no-declaradas)
7. [Seguridad del Propio Sistema (Meta-Seguridad)](#7-seguridad-del-propio-sistema-meta-seguridad)
8. [Configurabilidad y Vendor Lock-in](#8-configurabilidad-y-vendor-lock-in)
9. [Observaciones sobre la Documentación](#9-observaciones-sobre-la-documentación)
10. [Fortalezas del Proyecto](#10-fortalezas-del-proyecto)
11. [Priorización Recomendada](#11-priorización-recomendada)

---

## 1. Bug Crítico Activo (Blocker)

> ✅ **RESUELTO** - PR #24 mergeada el 2026-02-21 (commit `b62b0d3`). Rama eliminada.

### `MAX_DIFF_CHARS` no definida - `NameError` en runtime

**Fichero:** `src/ai.py`, líneas 83–86
**Rama afectada:** `fix/diff-truncation-feedback` (ya mergeada a `main`)

```python
# Línea 83 - la constante MAX_DIFF_CHARS no existe en ningún sitio del archivo
truncated_diff = diff_text[:MAX_DIFF_CHARS]
if original_len > MAX_DIFF_CHARS:
    chars_lost = original_len - MAX_DIFF_CHARS
```

La rama `fix/diff-truncation-feedback` introdujo el feedback visual de truncado pero olvidó definir la constante. La versión anterior tenía el literal `[:30000]` directamente en el slice. El código fallará con `NameError: name 'MAX_DIFF_CHARS' is not defined` en cualquier ejecución real.

**Impacto:** La herramienta es completamente no funcional en esta rama hasta que se defina la constante.

**Corrección sugerida:** Definir `MAX_DIFF_CHARS = 30_000` junto a las constantes FinOps existentes (línea 17).

---

## 2. Cobertura de Tests - Ausencia de Tests Unitarios Reales

**Estado actual:** No existe ningún fichero `test_*.py` en el directorio `tests/`.

El directorio `tests/` contiene únicamente:
- `__init__.py` (vacío)
- `fixtures/vulnerable_app/` - archivos vulnerables para demo manual

`pytest` está declarado como dependencia de desarrollo en `pyproject.toml` y el README menciona "Pytest (Testing unitario)" como parte del stack, pero no hay tests implementados.

**Escenarios de test mínimos para un TFM:**

| Módulo | Casos de test sugeridos |
|--------|------------------------|
| `security.py` | Diff con secreto AWS → debe retornar violación; diff limpio → lista vacía; líneas eliminadas (`-`) no deben detectarse |
| `security.py` | Config YAML inválida → `SecurityPolicyError`; YAML sin sección `blocklist` → error |
| `ingest.py` | Repo git inválido → `GitIngestError`; `is_ci()` con/sin `GITHUB_ACTIONS` en env |
| `ai.py` | JSON malformado del LLM → retorna `BLOCK` con score 10; respuesta como lista → normalización correcta |
| `main.py` | Diff vacío → exit 0; fallo AI + SKIP_SCAN → exit 0; violación regex → exit 1 |

Sin tests automatizados, la cadena CI/CD no puede garantizar que los cambios no rompan funcionalidad existente. Para una defensa de TFM, la ausencia de tests es una debilidad argumentativa significativa.

---

## 3. Inconsistencias entre Configuración y Código

### 3.1 - `action.yml` referencia variables inexistentes

> ✅ **RESUELTO** - Verificado en GitHub `main` el 2026-02-21. `action.yml` usa correctamente `openrouter_api_key` / `OPENROUTER_API_KEY`. El autor también fue actualizado a "Óscar Sánchez Pérez".

**Fichero:** `action.yml`

```yaml
inputs:
  openai_api_key:
    description: "OpenAI API key for AI analysis"
    required: true
env:
  OPENAI_API_KEY: ${{ inputs.openai_api_key }}
```

El código fuente (`src/ai.py`) usa exclusivamente `OPENROUTER_API_KEY`, no `OPENAI_API_KEY`. Este `action.yml` nunca funcionaría como GitHub Action publicada porque inyectaría una variable de entorno que el código no lee.

Además, el workflow CI/CD real (`.github/workflows/opsguard.yml`) no usa `action.yml` en absoluto - instala dependencias manualmente con Poetry. El `action.yml` parece un artefacto de una iteración anterior no eliminado.

### 3.2 - `OPSGUARD_RISK_THRESHOLD` definido pero ignorado

**Fichero:** `.github/workflows/opsguard.yml`, línea 40

```yaml
env:
  OPSGUARD_RISK_THRESHOLD: 7
```

**Fichero:** `src/main.py`, línea 98

```python
if verdict == "BLOCK" or risk_score >= 7:  # 7 hardcodeado
```

El threshold está hardcodeado en el código. La variable de entorno `OPSGUARD_RISK_THRESHOLD` definida en el workflow nunca se lee desde `os.getenv()`. El sistema no es configurable sin modificar el código fuente.

### 3.3 - `pull-requests: write` declarado pero sin uso

**Fichero:** `.github/workflows/opsguard.yml`, línea 16

```yaml
permissions:
  pull-requests: write # Necesario para comentar en el PR (Futuro)
```

El permiso está declarado con un comentario que lo reconoce como funcionalidad futura. Conceder permisos no utilizados viola el principio de mínimo privilegio. Debe eliminarse hasta que se implemente la funcionalidad de comentarios.

---

## 4. Brechas entre ADRs y la Implementación Real

### 4.1 - ADR-0003: Modos de Telemetría no implementados

**ADR-0003** define tres modos de operación:
1. **Verbose (default)**: Telemetría completa en logs estructurados
2. **Summary**: Solo métricas agregadas
3. **Silent**: Sin telemetría

**ADR-0003** también especifica el formato de salida como JSON estructurado:
```json
{
  "telemetry": {
    "model": "...",
    "input_tokens": 1542,
    "ttft_ms": 234,
    ...
  }
}
```

**Implementación real (`src/ai.py`):** Un único modo con `print()` de texto plano con códigos ANSI en Markdown. No hay JSON, no hay modos configurables, no hay `ttft` (Time-To-First-Token).

Esta brecha reduce el valor argumentativo del ADR como documento de decisión arquitectónica, ya que describe una arquitectura que no existe.

### 4.2 - ADR-0003: `ttft` (Time-To-First-Token) no capturado

El ADR especifica explícitamente `ttft_ms` como métrica. El cliente OpenAI SDK permite capturar este dato mediante streaming. La implementación actual solo mide la latencia total (`end_time - start_time`), que no equivale al TTFT.

### 4.3 - ADR-0002: Inconsistencia de idioma en el propio código

El ADR-0002 establece que los comentarios en código deben estar en inglés (estándar de industria). Sin embargo, `src/main.py`, `src/ai.py` e `src/ingest.py` contienen comentarios mezclados en español e inglés:

```python
# src/main.py
# Esto lanza una excepción 'Exit' que debemos dejar pasar
# Re-lanzamos la señal de salida limpia para que Typer termine con código 0.

# src/ai.py
# Mantenemos Gemini Flash 2.0 por su ventana de contexto y capacidad de razonamiento
# Cálculo de costes con precisión float
```

---

## 5. Calidad del Código - Deuda Técnica Menor

### 5.1 - Mezcla de `print()` y `console.print()` (Rich)

`src/ai.py` usa `print()` estándar para toda la telemetría y mensajes de depuración. `src/console_ui.py` usa Rich. Esta inconsistencia significa que parte de la salida bypasea el sistema de UI centralizado, imposibilitando añadir colores, redirección o formateo consistente a esos mensajes.

### 5.2 - Lógica de `SKIP_SCAN` frágil (String Matching sobre Excepciones)

**Fichero:** `src/main.py`, línea 61

```python
if "SKIP_SCAN" in str(e):
    print(f"⏭️  {e}")
    raise typer.Exit(code=0)
```

Detectar el tipo de evento via `str(e)` que contiene la cadena `"SKIP_SCAN"` es una práctica de bajo nivel. Un cambio en el mensaje de error en `ingest.py` rompería silenciosamente esta lógica. La solución correcta es una excepción personalizada (e.g., `class SkipScanSignal(GitIngestError)`).

### 5.3 - `except AttributeError` como catch de error de diseño

**Fichero:** `src/main.py`, línea 58

```python
except AttributeError:
    typer.secho("❌ API Mismatch: Asegúrate de que GitManager tenga 'get_staged_files()'.")
```

Este bloque captura un error de programación (método no existente en `GitManager`) en tiempo de ejecución. Este tipo de problema debería detectarse en tests, no con error handling defensivo en producción.

### 5.4 - `src/net_diag.py` sin integración documentada

Este fichero existe en `src/` pero no está referenciado en el README, los ADRs, ni importado desde ningún otro módulo. No tiene tests. No está claro si es funcionalidad productiva, código de ejemplo, o un artefacto de desarrollo. Su presencia en `src/` (en lugar de `scripts/` o similar) puede confundir a los evaluadores.

### 5.5 - Visualización FinOps con ANSI raw en lugar de Rich

**Fichero:** `src/ai.py`, líneas 116–124

```python
print(f"""
\033[92m### 💰 FinOps Telemetry
| Metric | Value | Unit Cost |
...
\033[0m""")
```

Se usan códigos de escape ANSI manualmente cuando el proyecto ya dispone de Rich como dependencia. Esto es inconsistente y los códigos ANSI pueden aparecer literalmente en logs de CI/CD según la configuración del terminal.

---

## 6. Dependencias no Declaradas

> ✅ **RESUELTO** - PR #23 mergeada el 2026-02-21 (commit `d6f6189`). Rama eliminada.

**Fichero:** `src/main.py`, línea 32

```python
import pathspec
```

`pathspec` se importa en `main.py` pero **no está declarado** en `pyproject.toml`. La herramienta fallará con `ModuleNotFoundError` en cualquier entorno limpio donde se haga `poetry install`.

**Verificación:**
```toml
# pyproject.toml - dependencias actuales
[tool.poetry.dependencies]
python = "^3.11"
typer, pydantic, gitpython, openai, pyyaml, python-dotenv, rich
# pathspec - AUSENTE
```

---

## 7. Seguridad del Propio Sistema (Meta-Seguridad)

### 7.1 - El System Prompt revela el contexto de la herramienta

```python
SYSTEM_PROMPT = """
CONTEXT: You are auditing the source code of "OpsGuard", a DevSecOps CLI tool.
CRITICAL CONTEXTUAL RULES:
1. Tooling Logic is SAFE: Code that implements file filtering [...] is INTENDED FUNCTIONALITY.
   Do NOT flag this as a "Security Bypass" or "Malicious Filtering".
```

Las reglas contextuales que previenen falsos positivos son razonables, pero revelan el nombre y naturaleza de la herramienta al LLM. Un atacante que conozca este prompt podría camuflar código malicioso como "lógica de filtrado de OpsGuard" para evitar la detección. Para un TFM es aceptable, pero en un sistema de producción real, el contexto debería ser más genérico.

### 7.2 - Truncado del diff puede omitir vulnerabilidades

El truncado a `MAX_DIFF_CHARS` caracteres por razones de coste puede hacer que el AI Engine no analice el final del diff, donde podrían existir vulnerabilidades. No se informa al usuario del porcentaje de código que quedó sin analizar ni si los hallazgos cubrieron el diff completo.

### 7.3 - `fail closed` inconsistente ante errores de red

El principio "Fail Closed" se aplica correctamente en el bloque `except Exception` de `ai.py` (retorna `BLOCK`). Sin embargo, si el LLM retorna un JSON válido pero con estructura inesperada, el `parsed_data.get("verdict", "BLOCK")` retorna `BLOCK` correctamente. Pero si `parsed_data` fuera un tipo no-dict (e.g., un `int`), el `.get()` lanzaría `AttributeError` que sería capturado por el `except Exception` general → `BLOCK`. La lógica de normalización para el caso de lista (`isinstance(parsed_data, list)`) no cubre todos los tipos posibles.

---

## 8. Configurabilidad y Vendor Lock-in

### 8.1 - Modelo hardcodeado sin abstracción

```python
# src/ai.py, línea 72
self.model = "google/gemini-2.0-flash-001"
```

El modelo está hardcodeado. No puede cambiarse sin modificar el código. El ADR-0003 menciona una "Comparativa Gemini Flash vs Claude Sonnet vs Claude Haiku" como aplicación prevista de la telemetría, pero la herramienta no permite seleccionar el modelo en tiempo de ejecución (e.g., `--model` como argumento CLI o variable de entorno).

### 8.2 - Threshold de riesgo hardcodeado

El umbral `>= 7` aparece en tres lugares conceptuales (código, workflow, README) pero solo está codificado en el fuente. Un cambio de política de seguridad requiere modificar código, no solo configuración.

### 8.3 - Sin soporte para múltiples proveedores LLM

> ⬛ **DESCARTADO por decisión de arquitectura** - Revisión técnica 2026-02-21. Decider: Óscar Sánchez Pérez.

#### Propuesta revisada

Durante la sesión de auditoría técnica asistida por IA, se propuso implementar un patrón de abstracción de proveedor LLM mediante una interfaz `LLMProvider`:

```python
# Propuesta discutida y descartada
class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...

class OpenRouterProvider(LLMProvider): ...
class AnthropicProvider(LLMProvider): ...
```

La motivación era permitir cambiar de proveedor (Anthropic, OpenAI, Google directo) sin modificar `AIEngine`.

#### Decisión y razonamiento

**Propuesta descartada.** La premisa de la mejora es incorrecta en el contexto de este sistema:

1. **OpenRouter ya es la capa de abstracción de proveedores.** Su API unificada, compatible con el cliente `openai` SDK, permite acceder a modelos de Google, Anthropic, Meta, Mistral y cualquier otro proveedor simplemente cambiando el identificador de modelo. No hay necesidad de una interfaz propia porque el contrato que resuelve ese problema ya existe a nivel de infraestructura.

2. **Abstraer lo que ya está abstraído introduce complejidad sin valor.** Una interfaz `LLMProvider` requeriría implementar al menos dos providers concretos para tener sentido. Con un único proveedor real (OpenRouter), la interfaz existiría únicamente "por si acaso" - un anti-patrón de diseño conocido como *speculative generality*.

3. **El caso de uso real ya está cubierto.** La necesidad concreta identificada en §8.1 (cambiar de modelo sin tocar código) queda resuelta por `OPSGUARD_MODEL` env var (PR #36). El cambio de proveedor completo es un escenario hipotético sin demanda real en este proyecto.

#### Conclusión

La abstracción propuesta es técnicamente válida como ejercicio académico, pero su implementación en este sistema añadiría código cuya única función sería existir. Se documenta el razonamiento para evidenciar que la ausencia de esta abstracción es una **decisión de diseño consciente**, no una omisión.

---

## 9. Observaciones sobre la Documentación

### 9.1 - `pyproject.toml` tiene datos de autor sin personalizar

```toml
authors = ["Your Name <you@example.com>"]
```

El placeholder no fue reemplazado con los datos reales del autor. Es un detalle menor pero visible en la evaluación.

### 9.2 - URL malformada en README

```markdown
git clone [https://github.com/oscaar90/OpsGuard-AI.git](https://github.com/...)
```

El comando `git clone` en el README tiene una URL en formato Markdown link (`[texto](url)`) en lugar de la URL plana. El comando copiado literalmente fallaría.

### 9.3 - `docs/evidence/` referenciada pero vacía (o sin contenido verificable)

El README enlaza a `/docs/evidence` como colección de "logs reales y capturas de funcionamiento". Si este directorio está vacío o no contiene evidencias verificables, debilita la credibilidad del apartado de "Evidencias de Ejecución" ante el tribunal.

### 9.4 - ADRs sin fecha ni número de revisión

Los ADRs siguen la convención de nombre `000X-nombre.md` pero no incluyen campos como `Date`, `Revised`, o `Deciders` que son estándar en formatos ADR como el de Michael Nygard. Añadir estos campos aumentaría el rigor del documento.

---

## 10. Fortalezas del Proyecto

Para equilibrar el análisis, estas son las áreas donde el proyecto demuestra solidez técnica:

- **Arquitectura Two-Gate correctamente razonada.** El patrón Local Gatekeeper (ADR-0001) es arquitectónicamente sólido: detectar secretos localmente antes de enviarlos a un LLM externo es la decisión correcta de seguridad.
- **`security.py` bien implementado.** Excepción personalizada, carga de config con validación, compilación de regex para rendimiento, escaneo solo de líneas añadidas (`+`) - todo correcto.
- **`ingest.py` gestiona bien los entornos duales.** La distinción local/CI mediante `is_ci()` y la lectura del `GITHUB_EVENT_PATH` es una solución práctica y robusta.
- **Fail Closed principle aplicado.** Ante cualquier error del AI Engine, el sistema bloquea el pipeline. Es la decisión de seguridad correcta.
- **FinOps con datos reales.** Calcular y mostrar el coste real por ejecución (aunque con presentación mejorable) es un diferenciador válido para la argumentación del TFM.
- **ADR-0002 bien justificado.** La decisión de usar prompts en inglés está respaldada con argumentos técnicos medibles (tokenización, benchmarks).
- **`pathspec` + `.opsguardignore`** es un mecanismo de filtrado elegante y coherente con la UX de herramientas como `.gitignore`.

---

## 11. Priorización Recomendada

| Prioridad | Área | Estado |
|-----------|------|--------|
| ~~🔴 **BLOCKER**~~ | ~~Definir `MAX_DIFF_CHARS` en `src/ai.py`~~ | ✅ PR #24 |
| ~~🔴 **BLOCKER**~~ | ~~Añadir `pathspec` a `pyproject.toml`~~ | ✅ PR #23 |
| ~~🟠 **ALTO**~~ | ~~Escribir tests unitarios para `security.py`~~ | ✅ PR #25 |
| ~~🟠 **ALTO**~~ | ~~Leer `OPSGUARD_RISK_THRESHOLD` desde `os.getenv()`~~ | ✅ PR #26 |
| ~~🟠 **ALTO**~~ | ~~Corregir `action.yml` (referencia a `OPENAI_API_KEY`)~~ | ✅ PR #21 (previo) |
| ~~🟡 **MEDIO**~~ | ~~Eliminar `pull-requests: write` del workflow~~ | ✅ PR #27 |
| ~~🟡 **MEDIO**~~ | ~~Reemplazar `SKIP_SCAN` string matching con excepción tipada~~ | ✅ PR #29 |
| ~~🟡 **MEDIO**~~ | ~~Alinear telemetría en `ai.py` con ADR-0003 (modos + Rich UI)~~ | ✅ PR #30 |
| ~~🟡 **MEDIO**~~ | ~~Corregir URL de `git clone` en README~~ | ✅ PR #34 |
| ~~🟡 **MEDIO**~~ | ~~Añadir `Date` y `Deciders` a los ADRs~~ | ✅ PR #32 |
| ~~🟢 **BAJO**~~ | ~~Migrar `print()` de `ai.py` a `console.print()` de Rich~~ | ✅ PR #30 |
| ~~🟢 **BAJO**~~ | ~~Documentar o mover `src/net_diag.py`~~ | ✅ PR #35 |
| ~~🟢 **BAJO**~~ | ~~Personalizar `authors` en `pyproject.toml`~~ | ✅ PR #34/#35 |
| ~~🟢 **BAJO**~~ | ~~Homogeneizar idioma de comentarios (inglés) según ADR-0002~~ | ✅ PR #37 |
| ~~🟢 **BAJO**~~ | ~~Modelo LLM hardcodeado - leer desde `OPSGUARD_MODEL` env var~~ | ✅ PR #36 |
| ⬛ **DESCARTADO** | Abstracción `LLMProvider` (§8.3) - OpenRouter ya es la abstracción | No aplica |

---

*Revisión generada el 2026-02-21. Basada en análisis estático del código fuente sin ejecución del sistema.*
*Ciclo de correcciones cerrado el 2026-02-21. 14 de 15 puntos resueltos (1 descartado por no aplicar). PRs #23–#37.*
