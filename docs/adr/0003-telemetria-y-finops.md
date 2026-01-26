# ADR 0003: Estrategia de Telemetría y FinOps

## Estado
Aceptado

## Contexto
Los costes de inferencia de LLMs y la latencia son factores críticos para la adopción de OpsGuard-AI en pipelines de CI/CD reales. Las objeciones principales de los equipos de ingeniería ante herramientas basadas en LLM son:

1. **Coste impredecible**: Sin métricas, es imposible estimar el coste mensual de la herramienta
2. **Latencia excesiva**: Checks lentos bloquean el flujo de desarrollo y frustran a los desarrolladores
3. **Opacidad**: Sin datos empíricos, la selección de modelo (Gemini Flash vs Claude Sonnet) se basa en intuición

### Requisitos del proyecto académico:
- El Trabajo Fin de Máster (TFM) requiere justificación cuantitativa de las decisiones técnicas
- La comparativa de modelos debe basarse en datos reales, no en benchmarks teóricos
- El tribunal evaluará la metodología de medición y análisis de costes

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

### Aplicaciones previstas:
1. Comparativa Gemini Flash vs Claude Sonnet vs Claude Haiku
2. Análisis de correlación entre tamaño de código y consumo de tokens
3. Identificación de umbrales óptimos de timeout
4. Generación de gráficos de coste para la memoria del TFM
