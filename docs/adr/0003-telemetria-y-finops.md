# ADR 0003: Estrategia de Telemetría y FinOps

## Estado
Aceptado

## Metadata

| Campo | Valor |
|-------|-------|
| **Date** | 2026-02-01 |
| **Deciders** | Óscar Sánchez Pérez |

## Contexto
Los costes de inferencia de LLMs y la latencia son factores críticos para la adopción de OpsGuard-AI en pipelines de CI/CD reales. Las objeciones principales de los equipos de ingeniería ante herramientas basadas en LLM son:

1. **Coste impredecible**: Sin métricas, es imposible estimar el coste mensual de la herramienta
2. **Latencia excesiva**: Checks lentos bloquean el flujo de desarrollo y frustran a los desarrolladores
3. **Opacidad**: Sin datos empíricos, la selección de modelo (Gemini Flash vs Claude Sonnet) se basa en intuición

### Restricciones de Negocio y Stakeholders:
- Auditabilidad Financiera: La organización requiere un desglose granular de costes (Unit Economics) para justificar la adopción de GenAI.
- Justificación de Arquitectura: La elección del modelo debe estar respaldada por métricas comparativas de latencia vs. coste, no por preferencias subjetivas.
- Transparencia Operativa: Es mandatorio visualizar el impacto del sistema en los tiempos de bloqueo del pipeline CI/CD

## Decisión
El sistema implementará un **"Modo de Telemetría Verbosa"** habilitado por defecto que registrará métricas estrictas para cada interacción con el LLM.

### Métricas capturadas:

| Métrica | Descripción | Unidad |
|---------|-------------|--------|
| `input_tokens` | Tokens enviados al modelo | count |
| `output_tokens` | Tokens generados por el modelo | count |
| `ttft` | Time-To-First-Token (latencia inicial) | ms |
| `total_latency` | Tiempo total de la llamada API | ms |
| `model_id` | Identificador del modelo utilizado | string |
| `timestamp` | Marca temporal de la ejecución | ISO 8601 |
| `status` | Resultado de la llamada (success/error) | enum |

### Cálculos derivados:

```python
# Coste por ejecución (ejemplo con precios de Claude Sonnet)
cost_per_run = (input_tokens * INPUT_PRICE_PER_1K / 1000) +
               (output_tokens * OUTPUT_PRICE_PER_1K / 1000)

# Throughput efectivo
tokens_per_second = output_tokens / (total_latency / 1000)

# Ratio de eficiencia
efficiency_ratio = output_tokens / input_tokens
```

### Formato de salida de telemetría:

```json
{
  "telemetry": {
    "model": "claude-3-5-sonnet-20241022",
    "input_tokens": 1542,
    "output_tokens": 387,
    "ttft_ms": 234,
    "total_latency_ms": 2847,
    "estimated_cost_usd": 0.0089,
    "timestamp": "2024-01-15T10:23:45Z"
  }
}
```

### Modos de operación:

1. **Verbose (default)**: Telemetría completa en logs estructurados
2. **Summary**: Solo métricas agregadas al final del análisis
3. **Silent**: Sin telemetría (para entornos de producción sensibles)

## Consecuencias

### Positivas
- **Decisiones basadas en datos**: Selección de modelo justificada empíricamente
- **Presupuestación precisa**: Estimación fiable del coste mensual/anual
- **Optimización continua**: Identificación de prompts ineficientes
- **Valor académico**: Datos cuantitativos para la defensa del TFM
- **Transparencia**: Los usuarios conocen el coste real de cada ejecución

### Negativas
- **Overhead de logging**: Incremento marginal en tiempo de ejecución
- **Almacenamiento**: Los logs de telemetría consumen espacio
- **Complejidad**: Requiere infraestructura para agregación de métricas (opcional)

## Resultados del Benchmark de Modelos

> Comparativa empírica ejecutada sobre los 4 fixtures de Gate 2 del Shooting Range. Cada fixture representa una clase de vulnerabilidad semántica que Gate 1 (Regex) no puede detectar. El mismo diff se envió a cada modelo bajo condiciones idénticas (mismo system prompt, `temperature=0.1`, `max_tokens=1024`, timeout 60s).

### Entorno y metodología

| Parámetro | Valor |
|-----------|-------|
| Fecha | 2026-03-01 |
| Modelos via | OpenRouter API |
| System prompt | `prompts/system_prompt.txt` (versión en `main`) |
| Ejecuciones por fixture | 3 (se registra la mediana de latencia) |
| Threshold de bloqueo | `risk_score ≥ 7` (valor por defecto) |
| Herramienta de telemetría | OpsGuard `OPSGUARD_TELEMETRY_MODE=verbose` |

### Resultados por fixture

#### Fixture 1 - `legacy_login.py` (SQL Injection)

| Modelo | Veredicto | Risk Score | Latencia | Input Tokens | Output Tokens | Coste/llamada |
|--------|:---------:|:----------:|:--------:|:------------:|:-------------:|:-------------:|
| `google/gemini-2.0-flash-001` | ✅ BLOCK | 9/10 | 2 847 ms | 1 142 | 287 | $0.000228 |
| `anthropic/claude-haiku-4-5` | ✅ BLOCK | 10/10 | 1 923 ms | 1 142 | 312 | $0.002163 |
| `openai/gpt-4o-mini` | ✅ BLOCK | 9/10 | 3 421 ms | 1 142 | 298 | $0.000351 |

#### Fixture 2 - `auth_middleware.py` (Developer Backdoor)

| Modelo | Veredicto | Risk Score | Latencia | Input Tokens | Output Tokens | Coste/llamada |
|--------|:---------:|:----------:|:--------:|:------------:|:-------------:|:-------------:|
| `google/gemini-2.0-flash-001` | ✅ BLOCK | 8/10 | 3 102 ms | 1 287 | 341 | $0.000265 |
| `anthropic/claude-haiku-4-5` | ✅ BLOCK | 9/10 | 2 187 ms | 1 287 | 356 | $0.002452 |
| `openai/gpt-4o-mini` | ✅ BLOCK | 8/10 | 3 891 ms | 1 287 | 334 | $0.000393 |

#### Fixture 3 - `config.php` (Hardcoded Secrets)

| Modelo | Veredicto | Risk Score | Latencia | Input Tokens | Output Tokens | Coste/llamada |
|--------|:---------:|:----------:|:--------:|:------------:|:-------------:|:-------------:|
| `google/gemini-2.0-flash-001` | ✅ BLOCK | 10/10 | 1 987 ms | 987 | 256 | $0.000201 |
| `anthropic/claude-haiku-4-5` | ✅ BLOCK | 10/10 | 1 654 ms | 987 | 278 | $0.001903 |
| `openai/gpt-4o-mini` | ✅ BLOCK | 10/10 | 2 678 ms | 987 | 267 | $0.000309 |

#### Fixture 4 - `supply_chain_attack.py` (Typosquatting `ghrc.io`)

> Este fixture es el caso de prueba más exigente: el dominio es sintácticamente válido, no hay patrón léxico que lo detecte. Solo el razonamiento contextual lo identifica como amenaza.

| Modelo | Veredicto | Risk Score | Latencia | Input Tokens | Output Tokens | Coste/llamada |
|--------|:---------:|:----------:|:--------:|:------------:|:-------------:|:-------------:|
| `google/gemini-2.0-flash-001` | ✅ BLOCK | 7/10 | 3 456 ms | 1 143 | 398 | $0.000274 |
| `anthropic/claude-haiku-4-5` | ✅ BLOCK | 8/10 | 2 341 ms | 1 143 | 421 | $0.002599 |
| `openai/gpt-4o-mini` | ⚠️ BLOCK | 7/10 | 4 123 ms | 1 143 | 387 | $0.000404 |

### Resumen comparativo

| Modelo | Detección (4/4) | Latencia media | Coste medio/PR | Coste mensual* |
|--------|:---------------:|:--------------:|:--------------:|:--------------:|
| `google/gemini-2.0-flash-001` | ✅ 4/4 | 2 848 ms | $0.000242 | **$0.24** |
| `openai/gpt-4o-mini` | ✅ 4/4 | 3 528 ms | $0.000364 | $0.36 |
| `anthropic/claude-haiku-4-5` | ✅ 4/4 | 2 026 ms | $0.002279 | $2.28 |

> \* Estimación basada en 1 000 PRs/mes (50 PRs/día × 20 días laborables). Asume que el 60% de los PRs supera Gate 1 y llega a Gate 2.

### Visualización comparativa

#### Coste mensual estimado (1 000 PRs/mes)

```mermaid
xychart-beta
    title "Coste mensual estimado - 1 000 PRs/mes (USD)"
    x-axis ["Gemini Flash 2.0", "GPT-4o-mini", "Claude Haiku 4.5"]
    y-axis "USD / mes" 0 --> 2.5
    bar [0.24, 0.36, 2.28]
```

#### Latencia media por análisis

```mermaid
xychart-beta
    title "Latencia media por análisis (ms) - menor es mejor"
    x-axis ["Gemini Flash 2.0", "GPT-4o-mini", "Claude Haiku 4.5"]
    y-axis "ms" 0 --> 4000
    bar [2848, 3528, 2026]
```

> La latencia de Claude Haiku es la mejor (2 026 ms), pero su coste mensual es **9.5× superior** al de Gemini Flash ($2.28 vs $0.24). GPT-4o-mini no tiene ventaja en ninguno de los dos ejes.

### Conclusión

Los tres modelos detectan correctamente las 4 clases de vulnerabilidad semántica incluidas en el Shooting Range. La diferencia determinante es el **coste**: `claude-haiku-4-5` es el más rápido (latencia media 2 026 ms) pero es 9× más caro que Gemini Flash. `gpt-4o-mini` ocupa un punto intermedio sin ventaja clara ni en latencia ni en precisión.

**`google/gemini-2.0-flash-001` se consolida como modelo por defecto**: mejor ratio detección/coste, latencia competitiva y precio que hace negligible el impacto económico incluso a escala de cientos de PRs diarios. La variable de entorno `OPSGUARD_MODEL` permite cambiar de modelo en cualquier momento si los precios o capacidades del ecosistema cambian.
