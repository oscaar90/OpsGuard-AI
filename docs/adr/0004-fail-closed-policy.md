# ADR 0004: Política Fail-Closed en Gate 2

## Estado
Aceptado

## Metadata

| Campo | Valor |
|-------|-------|
| **Date** | 2026-03-01 |
| **Deciders** | Óscar Sánchez Pérez |

## Contexto

Gate 2 (`src/ai.py`) depende de una API externa (OpenRouter) para realizar el análisis semántico del diff. Esta dependencia introduce un punto de fallo ajeno al control del equipo: la API puede estar caída, el timeout puede agotarse, la respuesta puede llegar malformada o en un formato inesperado, o la API key puede haber expirado.

Cuando cualquiera de estos fallos ocurre en un sistema de seguridad, hay que tomar una decisión arquitectónica fundamental:

> **¿Debe el pipeline bloquearse o continuar cuando el motor de IA no puede emitir un veredicto?**

Las dos opciones son:

| Política | Comportamiento ante fallo | Principio que prioriza |
|----------|--------------------------|------------------------|
| **Fail-open** | El pipeline continúa (`APPROVE`) | Disponibilidad / velocidad de desarrollo |
| **Fail-closed** | El pipeline se bloquea (`BLOCK`, `risk_score: 10`) | Seguridad / defensa en profundidad |

## Decisión

OpsGuard implementa **fail-closed**: cualquier excepción no controlada en `analyze_diff()` retorna un veredicto de bloqueo con `risk_score: 10`, sin propagar la excepción al orquestador.

```python
except Exception as e:
    # Fail closed: any engine failure blocks the pipeline.
    return {
        "verdict": "BLOCK",
        "risk_score": 10,
        "explanation": f"Internal Engine Error: {str(e)}",
        "findings": [],
    }
```

El mismo principio aplica a fallos internos de parseo (JSON malformado, tipo de respuesta inesperado): en lugar de propagar la excepción, se retorna inmediatamente un veredicto de bloqueo.

## Justificación

OpsGuard es una **puerta de seguridad**, no un servicio de productividad. Su contrato con el equipo es: *"Si no puedo garantizar que el código es seguro, no dejo que pase."*

Un fallo silencioso en Gate 2 que permitiera el merge de código malicioso sería un fallo de seguridad. Un fallo en Gate 2 que bloquee temporalmente el pipeline es una interrupción operacional recuperable.

En sistemas de seguridad, la disponibilidad es secundaria a la integridad. Esta es la misma lógica que aplican los firewalls con su política por defecto `DENY ALL` o los validadores de certificados TLS que rechazan conexiones ante cualquier anomalía.

## Consecuencias

### Positivas
- **Seguridad garantizada ante fallos**: ningún PR puede pasar silenciosamente por un error técnico del motor de IA.
- **Comportamiento predecible**: los equipos saben que ante cualquier error del sistema, el pipeline se detiene - no pasa nada de forma inadvertida.
- **Sin superficie de ataque por degradación**: un atacante no puede provocar intencionadamente un fallo del motor (p.ej. enviando un diff que consuma todo el contexto) para que el sistema apruebe código malicioso por omisión.

### Negativas
- **Impacto en disponibilidad**: una caída de OpenRouter, un agotamiento de cuota o una expiración de la API key bloqueará **todos** los PRs del equipo hasta que se resuelva el problema operacional.
- **Falsos bloqueos no auditables**: el bloqueo por fallo de motor no genera findings técnicos - solo un mensaje de error interno. El equipo necesita monitorización externa (alertas de CI, dashboards) para distinguir un bloqueo por amenaza real de un bloqueo por fallo de infraestructura.

## Mitigaciones para producción

Para reducir el impacto de los fallos de disponibilidad sin sacrificar la política de seguridad:

1. **Monitorización del job `security-scan`**: distinguir en los dashboards de CI entre `exit 1` por amenaza detectada vs `exit 1` por error de motor (el mensaje de consola los diferencia).
2. **Configurar alertas de OpenRouter** para cuota y latencia anómala.
3. **Usar el modo `OPSGUARD_TELEMETRY_MODE=verbose`** en CI para que los logs incluyan el error exacto que causó el bloqueo.
4. **Timeout explícito de 60s** en el cliente OpenAI para evitar que el job de CI quede colgado indefinidamente.
