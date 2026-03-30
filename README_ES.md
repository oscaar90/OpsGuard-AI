# 🛡️ OpsGuard AI

> **El guardia de seguridad que nunca duerme, revisando tu código antes de que sea un problema.**

![Python](https://img.shields.io/badge/python-3.12-blue)
![Status](https://img.shields.io/badge/status-stable-green)
![CI/CD](https://img.shields.io/badge/github--actions-enabled-brightgreen)

---

## El problema que resuelve OpsGuard

Imagina que tienes un restaurante y cada día llegan nuevos ingredientes. Antes de meterlos en la cocina, alguien tiene que revisarlos para asegurarse de que no hay nada en mal estado. 

En el mundo del software pasa lo mismo. Los equipos escriben código nuevo todos los días y, por error o por prisa, a veces dejan brechas de seguridad abiertas (como credenciales olvidadas o fallos lógicos graves) que pueden ser explotadas por actores maliciosos.

**OpsGuard es el revisor en la puerta de tu infraestructura.** Analiza cada cambio en el código automáticamente y, si detecta un riesgo, bloquea la entrada antes de que llegue a producción y afecte a tus usuarios.

## ¿Cómo funciona? (El control del aeropuerto)

OpsGuard revisa tu código simulando el control de seguridad de un aeropuerto, en dos fases:

1. **El escáner de rayos X (Búsqueda ultrarrápida):** Revisa el código en milisegundos buscando cosas obvias y prohibidas, como contraseñas, tokens o claves secretas. Funciona 100% en local.
2. **El agente experto (Inteligencia Artificial):** Si el escáner no pita, una IA lee el código para entender el *contexto*. Busca trampas ocultas, errores de lógica o código generado por otras IAs (como Copilot) que parezca normal pero sea vulnerable.

**Si en cualquiera de las dos puertas se detecta un problema, el código no pasa.**

## ¿Por qué OpsGuard?

A diferencia de otras herramientas clásicas que solo buscan palabras exactas en un diccionario, OpsGuard **entiende** lo que hace el código.

- 🔒 **Privacidad local:** Las credenciales se detectan en tu propio entorno mediante análisis estático y nunca viajan a ninguna IA externa.
- 💸 **Coste-eficiente:** El análisis semántico tiene un coste marginal de aproximadamente $0.001 por cada revisión.
- 🤖 **Auditor de IA:** Detecta automáticamente vulnerabilidades introducidas por herramientas de autocompletado de código como Copilot o Cursor.
- 🔔 **Alertas integradas:** Al bloquear una amenaza, genera un informe detallado directamente como un Issue en GitHub con los pasos para su resolución.

📊 **[Ver comparativa con otras herramientas y métricas de rendimiento](./docs/benchmark-models.md)**

## Ejemplos de lo que detecta
- Contraseñas, Tokens, claves de APIs (AWS, Stripe, GitHub, etc.) o credenciales olvidadas en el código.
- Ataques de inyección (ej. SQL Injections).
- Puertas traseras ("Backdoors") dejadas activas para hacer pruebas.
- Errores tipográficos catastróficos que apuntan a servidores piratas (Typosquatting).

🔍 **[Ver casos reales de código bloqueado por OpsGuard](./docs/ejemplos-reales.md)**

## Ponlo a trabajar en 2 minutos

OpsGuard se instala directamente en tu repositorio de GitHub. No tienes que mantener servidores ni instalar nada raro.

1. Consigue una API Key gratuita en [OpenRouter](https://openrouter.ai).
2. Añádela a tu repositorio de GitHub en *Settings → Secrets* con el nombre `OPENROUTER_API_KEY`. *(Esto es lo que permite que la acción de GitHub se conecte a la IA y analice el código de forma automática cada vez que alguien intente subir cambios en un Pull Request).*
3. Crea un archivo llamado `.github/workflows/opsguard.yml` en tu repositorio y pega esto:

```yaml
name: OpsGuard Security Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: oscaar90/OpsGuard-AI@v1
        with:
          openrouter-api-key: ${{ secrets.OPENROUTER_API_KEY }}
```

**¡Ya está!** Tu código ahora tiene un guardia de seguridad revisando cada cambio 24/7.

---

## Documentación para Ingenieros

Si quieres meterte en las tripas técnicas del proyecto, aquí tienes todo el detalle:

- **[Guía de instalación y pruebas en local](./docs/guia-local.md)**
- **[Decisiones de Arquitectura (ADRs)](./docs/adr/)**
- **[Estrategia de Inteligencia Artificial (Prompts)](./prompts/)**
- **[Registro de Cambios (Changelog)](./CHANGELOG.md)**

---

## Licencia y Uso Comercial (Dual Licensing)

OpsGuard AI utiliza un modelo de **Licencia Dual**:

1. **Open Source (AGPLv3)**: Puedes usar, modificar y distribuir OpsGuard de forma gratuita bajo los términos de la [GNU Affero General Public License v3.0 (AGPLv3)](LICENSE). Ideal para proyectos personales, código abierto o pruebas no productivas. *(Nota: El uso de código bajo licencia AGPL en entornos corporativos suele requerir abrir el código fuente de los sistemas vinculados).*
2. **Licencia Comercial**: Si deseas utilizar OpsGuard en una empresa, integrarlo en flujos de trabajo corporativos cerrados o evitar las restricciones de la licencia AGPL (copyleft) en tu infraestructura privativa, **es necesario adquirir una Licencia Comercial**.

📧 Para obtener permisos comerciales o resolver dudas sobre licencias, contacta en: **oscar@oscarai.tech**