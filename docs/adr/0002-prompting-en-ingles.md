# ADR 0002: Ingeniería de Prompts en Inglés

## Estado
Aceptado

## Contexto
OpsGuard-AI utiliza modelos de lenguaje (Claude de Anthropic, Gemini de Google) como motor de razonamiento para detectar vulnerabilidades de seguridad en código. La elección del idioma para los prompts del sistema tiene implicaciones directas en:

1. **Consumo de tokens**: Los modelos tokenizadores están optimizados para inglés. El texto en español genera más tokens para expresar el mismo contenido semántico.

2. **Calidad de respuestas**: Los LLMs han sido entrenados predominantemente con corpus en inglés, especialmente en dominios técnicos como seguridad informática y desarrollo de software.

3. **Costes operativos**: Mayor número de tokens implica mayor coste por inferencia (pricing por token).

4. **Latencia**: Más tokens de entrada y salida incrementan el tiempo de procesamiento.

### Datos empíricos considerados:
- La tokenización de texto técnico en español puede requerir entre 15-30% más tokens que su equivalente en inglés
- Los benchmarks de razonamiento técnico muestran mejor rendimiento en inglés
- La documentación técnica de referencia (OWASP, CVE, CWE) está mayoritariamente en inglés

## Decisión
Todos los **prompts del sistema** enviados al LLM serán redactados en **inglés técnico**.

### Alcance de la decisión:

| Componente | Idioma | Justificación |
|------------|--------|---------------|
| System prompts | Inglés | Optimización de tokens y calidad |
| Instrucciones al LLM | Inglés | Mejor interpretación por el modelo |
| Categorías de vulnerabilidades | Inglés | Alineación con estándares (OWASP, CWE) |
| ADRs y documentación | Español | Requisito académico del Tribunal |
| README del proyecto | Español | Audiencia objetivo universitaria |
| Comentarios en código | Inglés | Estándar de la industria |

### Estructura de prompts:
```
[SYSTEM PROMPT - English]
You are a security analyst specialized in detecting vulnerabilities...

[USER INPUT - Mixed]
Analyze the following code for security issues:
{código_del_usuario}

[RESPONSE - English]
Structured analysis in English for consistent parsing
```

## Consecuencias

### Positivas
- **Reducción de costes**: Menor consumo de tokens por análisis (~15-20% de ahorro estimado)
- **Menor latencia**: Tiempos de respuesta más rápidos en CI/CD
- **Mayor precisión**: Reducción de interpretaciones erróneas o "alucinaciones"
- **Consistencia**: Respuestas estructuradas más predecibles para parsing automatizado
- **Alineación con estándares**: Terminología compatible con bases de datos de vulnerabilidades

### Negativas
- **Barrera idiomática**: Desarrolladores no angloparlantes pueden tener dificultades para depurar prompts
- **Documentación dual**: Necesidad de mantener documentación en dos idiomas
- **Curva de aprendizaje**: Requiere competencia en inglés técnico para modificar prompts

### Notas de implementación
- Los mensajes de error mostrados al usuario final pueden localizarse a español
- Los reportes generados mantendrán terminología técnica en inglés para precisión
