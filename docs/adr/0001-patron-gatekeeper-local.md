# ADR 0001: Patrón Gatekeeper Local

## Estado
Aceptado

## Contexto
El sistema OpsGuard-AI es una GitHub Action que utiliza modelos de lenguaje (LLMs) para detectar vulnerabilidades de seguridad en código fuente. Sin embargo, enviar código que potencialmente contiene secretos (claves API, contraseñas, tokens de acceso) a una API externa de LLM constituye en sí mismo una fuga de datos sensibles.

Este problema presenta un dilema arquitectónico: necesitamos la capacidad analítica del LLM para detectar patrones complejos de vulnerabilidades, pero no podemos exponerle directamente código que contenga credenciales en texto plano.

### Restricciones identificadas:
- El código analizado puede contener secretos hardcodeados
- Las APIs de LLM (Claude, Gemini) procesan datos en servidores externos
- El envío de secretos a terceros viola políticas de seguridad corporativas
- La detección de secretos mediante LLM es redundante cuando existen soluciones deterministas probadas

## Decisión
Implementaremos una capa de **"Gatekeeper Local"** que actúa como filtro previo antes de cualquier comunicación con APIs externas de LLM.

### Arquitectura de la solución:

1. **Capa de Detección Local (Pre-LLM)**
   - Utiliza expresiones regulares (Regex) y reglas deterministas
   - Detecta patrones conocidos de secretos: API keys, tokens JWT, contraseñas en variables de entorno, etc.
   - Se ejecuta completamente dentro del contenedor de la GitHub Action

2. **Comportamiento ante detección de secretos (Hard Fail)**
   - Si se detecta un secreto con alta confianza, el pipeline falla inmediatamente
   - El LLM **nunca** es contactado cuando hay secretos confirmados
   - Se genera un reporte local con la ubicación y tipo de secreto detectado

3. **Flujo de datos**
   ```
   Código → Gatekeeper Local → [Secreto detectado?]
                                    ├── SÍ → Hard Fail (sin contactar LLM)
                                    └── NO → Enviar a LLM para análisis profundo
   ```

## Consecuencias

### Positivas
- **Seguridad garantizada**: Los secretos nunca abandonan el entorno de ejecución local
- **Reducción de costes**: Evita llamadas innecesarias al LLM cuando hay fallos obvios
- **Latencia reducida**: La detección local es instantánea comparada con llamadas API
- **Cumplimiento normativo**: Facilita el cumplimiento de políticas de no-exposición de datos

### Negativas
- **Mantenimiento de reglas**: Las expresiones regulares requieren actualización periódica
- **Falsos positivos**: Algunos patrones pueden coincidir con datos no sensibles
- **Complejidad añadida**: Introduce una capa adicional en la arquitectura

### Riesgos mitigados
- Fuga de credenciales a proveedores de LLM externos
- Violación de acuerdos de confidencialidad
- Exposición accidental de secretos en logs de terceros
