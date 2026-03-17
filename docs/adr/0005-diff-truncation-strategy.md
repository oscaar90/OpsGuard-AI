# ADR 0005: Estrategia de Truncado de Diff

## Estado
Aceptado - Revisión pendiente en v1.0

## Metadata

| Campo | Valor |
|-------|-------|
| **Date** | 2026-03-01 |
| **Deciders** | Óscar Sánchez Pérez |

## Contexto

El motor de Gate 2 (`src/ai.py`) envía el diff completo del PR al LLM para su análisis semántico. Los diffs de PRs reales pueden variar drásticamente en tamaño: desde unos pocos cientos de caracteres hasta cientos de miles en PRs que afectan a ficheros generados, migraciones de base de datos o refactorizaciones masivas.

Enviar diffs sin límite de tamaño al LLM presenta tres problemas concretos:

1. **Coste impredecible**: el precio se factura por tokens de entrada. Un diff de 200 KB con `google/gemini-2.0-flash-001` puede costar 50× más que uno de 4 KB.
2. **Límite de contexto**: aunque Gemini Flash 2.0 soporta ~1M tokens, otros modelos (Claude Haiku, GPT-4o-mini) tienen ventanas de 128K–200K tokens. Una arquitectura que depende de ventanas largas no es portable.
3. **Degradación de calidad**: los LLMs muestran pérdida de atención ("lost in the middle") en contextos muy largos, reduciendo la precisión de detección.

## Decisión

Se aplica un **truncado simple por longitud de caracteres** con límite fijo de `MAX_DIFF_CHARS = 30_000`.

El truncado se aplica sobre el string del diff antes de construir el mensaje enviado al LLM:

```python
truncated_diff = diff_text[:MAX_DIFF_CHARS]
```

Si el diff supera el límite, se descarta la parte final y se emite una advertencia en consola con los caracteres perdidos. El umbral de 30 000 caracteres equivale aproximadamente a 7 500 tokens (ratio ~4 chars/token), dentro del rango de coste objetivo de $0.001 por análisis.

## Alternativas consideradas

| Alternativa | Descripción | Motivo de descarte |
|-------------|-------------|-------------------|
| **Sin límite** | Enviar el diff completo siempre | Coste y latencia impredecibles en PRs grandes |
| **Chunking secuencial** | Dividir en bloques de 30K y analizar cada uno | Múltiples llamadas al LLM por PR; coste multiplicado |
| **Priorización por hunk** | Ordenar los hunks por número de líneas añadidas y tomar los más relevantes | Mayor complejidad de parseo; valor marginal no justificado en v1 |
| **Resumen previo** | Resumir el diff con un LLM barato antes del análisis de seguridad | Dos llamadas por PR; el resumen puede ocultar el contexto de seguridad |

## Consecuencias

### Positivas
- **Coste predecible**: el límite superior de coste por análisis es determinista.
- **Latencia acotada**: el tiempo de análisis del LLM no escala con el tamaño del PR.
- **Compatibilidad de modelos**: cualquier modelo con ventana ≥ 32K tokens puede sustituir al modelo por defecto sin cambios de código.

### Negativas
- **Cobertura parcial en PRs grandes**: las vulnerabilidades en la segunda mitad de un diff grande quedan fuera del análisis de Gate 2. Gate 1 (regex) sigue analizando el diff completo, por lo que los secretos estructurales siguen detectándose.
- **Descarte silencioso**: el truncado no es un fallo explícito - el pipeline continúa con análisis parcial. El aviso en consola es la única señal para el desarrollador.

### Deuda técnica documentada

Este truncado es una solución válida para v1 pero debería revisarse antes de una release de producción amplia. La estrategia recomendada para v2 es **priorización por hunk**: parsear el diff, ordenar los hunks por número de líneas añadidas (descendente) y construir el payload hasta `MAX_DIFF_CHARS`, garantizando que los cambios más sustanciales siempre quedan dentro del contexto enviado al LLM.
