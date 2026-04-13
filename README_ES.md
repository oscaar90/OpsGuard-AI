<p align="center">
  <strong>🛡️ OpsGuard AI</strong>
  <br/>
  Puerta de seguridad con IA para GitHub Actions que bloquea pull requests vulnerables antes del merge.
  <br/>
  <em>Primero detección local de secretos. Después revisión semántica de AppSec.</em>
</p>

<p align="center">
  <a href="https://github.com/oscaar90/OpsGuard-AI/stargazers"><img src="https://img.shields.io/github/stars/oscaar90/OpsGuard-AI?style=social" alt="GitHub stars"/></a>
  <a href="https://github.com/oscaar90/OpsGuard-AI/blob/main/LICENSE"><img src="https://img.shields.io/github/license/oscaar90/OpsGuard-AI" alt="License"/></a>
  <a href="https://github.com/oscaar90/OpsGuard-AI/actions"><img src="https://img.shields.io/github/actions/workflow/status/oscaar90/OpsGuard-AI/ci.yml?label=CI" alt="CI"/></a>
  <a href="https://github.com/oscaar90/OpsGuard-AI/issues"><img src="https://img.shields.io/github/issues/oscaar90/OpsGuard-AI" alt="Issues"/></a>
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/status-stable-brightgreen" alt="Status"/>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README_ES.md">Español</a>
</p>

<p align="center">
  <strong>Diseñado para PRs de GitHub</strong> · <strong>Los secretos se detectan primero en local</strong> · <strong>~$0.001 por escaneo semántico</strong> · <strong>Útil contra código inseguro generado por IA</strong>
</p>

---

## Por Qué La Gente Prueba OpsGuard

OpsGuard es una puerta de seguridad en dos etapas para pull requests:

- **Gate 1** detecta secretos hardcodeados y patrones conocidos como peligrosos en local, en milisegundos.
- **Gate 2** envía el diff a un LLM para revisar fallos lógicos y vulnerabilidades sutiles con contexto.

Los escáneres tradicionales se limitan en gran parte a buscar patrones. **OpsGuard también razona sobre la intención.**

Eso lo hace útil para el tipo de cambios que cada vez se cuelan más en los repositorios:

- Claves AWS hardcodeadas, tokens de GitHub y secretos de APIs
- SQL injection y bypasses de autenticación
- Typosquatting en código de despliegue y cadena de suministro
- Código vulnerable introducido por Copilot, Cursor, Devin o agentes autónomos de programación

---

## Véelo En Acción

![OpsGuard bloqueando una PR maliciosa](./docs/assets/demo.gif)

Ejemplo: una pull request añade una puerta trasera de desarrollador.

```python
def validate_request(headers):
    if headers.get("X-DEBUG-MODE") == "true":
        return True
```

OpsGuard deja pasar el Gate 1, envía el diff al Gate 2 y bloquea la PR con un hallazgo semántico:

```text
Veredicto: BLOCK
Puntuación de riesgo: 8/10
Problema: Puerta trasera de desarrollador vía cabecera X-DEBUG-MODE
```

Más ejemplos:

- [Casos reales bloqueados](./docs/ejemplos-reales.md)
- [Benchmark y comparación de modelos](./docs/benchmark-models.md)
- [Inventario de fixtures / shooting range](./tests/fixtures/README.md)

---

## Por Qué Destaca

- **Arquitectura en dos etapas**: primero comprobaciones deterministas y baratas; después razonamiento semántico.
- **Adopción con poca fricción**: se instala como GitHub Action en unas pocas líneas.
- **Diseño consciente de la privacidad**: los secretos obvios se detectan antes de cualquier llamada a un LLM.
- **Pensado para el modelo de amenaza actual**: las PRs inseguras ya no las escriben solo humanos.

Aquí es donde OpsGuard es más fuerte: **revisión de seguridad para código que parece sintácticamente normal pero es operativamente peligroso**.

---

## Pruébalo En 2 Minutos

1. Consigue una API key gratuita en [OpenRouter](https://openrouter.ai).
2. Añádela a los secretos de tu repositorio como `OPENROUTER_API_KEY`.
3. Crea `.github/workflows/opsguard.yml`:

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

Cada nueva pull request pasará por:

```text
Git Diff -> Gate 1: Regex local -> Gate 2: Revisión con LLM -> APPROVE / BLOCK
```

---

## Qué Detecta

### Gate 1: detección determinista local

- Claves de acceso AWS
- Tokens de GitHub
- Claves de Stripe
- Contraseñas y secretos hardcodeados genéricos
- Claves privadas

Las reglas viven en [`opsguard.yml`](./opsguard.yml).

### Gate 2: análisis semántico

- SQL injection
- Puertas traseras de desarrollador
- Bypasses de autenticación peligrosos
- Typosquatting en la cadena de suministro
- Lógica insegura generada por IA

Los ejemplos están documentados en [docs/ejemplos-reales.md](./docs/ejemplos-reales.md).

---

## Demo Rápida En Local

Si quieres probarlo antes de conectarlo a un repo real:

```bash
git clone https://github.com/oscaar90/OpsGuard-AI.git
cd OpsGuard-AI
poetry install
cp .env.example .env
```

Añade tu `OPENROUTER_API_KEY` al `.env` y prueba un fixture:

```bash
cp tests/fixtures/vulnerable_app/legacy_login.py src/legacy_login.py
git add src/legacy_login.py
poetry run opsguard scan
```

Resultado esperado: Gate 1 pasa y Gate 2 bloquea la SQL injection.

Guía local completa:

- [Guía de instalación y pruebas en local](./docs/guia-local.md)

---

## Qué Pasa Cuando Bloquea

- El job de GitHub Actions falla
- La CLI imprime una puntuación de riesgo y una explicación de seguridad
- Los hallazgos se muestran con archivo, severidad y descripción del problema
- La PR no pasa silenciosamente ante un fallo del LLM: OpsGuard es **fail-closed**

Decisiones clave de diseño:

- Gate 1 siempre se ejecuta primero en local
- Los prompts se mantienen en inglés por consistencia y eficiencia de tokens
- Los errores de IA devuelven `BLOCK`, no `APPROVE`
- Los diffs grandes se truncan para mantener latencia y coste predecibles

Consulta los ADRs en [`docs/adr/`](./docs/adr/).

---

## Para Quién Es

- Equipos que usan **GitHub Actions** como puerta de CI
- Startups sin una persona dedicada a AppSec
- Equipos que envían mucho **código asistido por IA**
- Repositorios que quieren una puerta de seguridad ligera antes de herramientas más pesadas

OpsGuard no intenta sustituir a todos los productos SAST. Intenta ser la **puerta rápida, barata y siempre activa** que detecta pull requests arriesgadas antes del merge.

---

## Comparativa

| Función | OpsGuard AI | Snyk | SonarQube | Semgrep |
|---------|:-----------:|:----:|:---------:|:-------:|
| Análisis semántico con LLM | ✅ | ❌ | ❌ | ❌ |
| Configuración como GitHub Action | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Puerta local de secretos | ✅ | ✅ | ❌ | ✅ |
| Enfoque sobre revisión de código generado por IA | ✅ | ❌ | ❌ | ❌ |
| Coste optimizado por escaneo | ✅ | ❌ | ❌ | ❌ |

Para la metodología del benchmark y sus resultados, consulta [docs/benchmark-models.md](./docs/benchmark-models.md).

---

## Documentación

- [Guía de instalación y pruebas en local](./docs/guia-local.md)
- [Casos reales bloqueados](./docs/ejemplos-reales.md)
- [Benchmark y comparación de modelos](./docs/benchmark-models.md)
- [Registros de decisiones de arquitectura](./docs/adr/)
- [Estrategia de prompts y artefactos de IA](./prompts/)
- [Changelog](./CHANGELOG.md)

---

## Licencia

OpsGuard AI utiliza un **modelo de doble licencia**:

- **Open Source (AGPLv3)** para proyectos personales, open source y uso no productivo
- **Licencia Comercial** para entornos corporativos cerrados o requisitos incompatibles con copyleft

Para licenciamiento comercial: **oscar@oscarai.tech**

---

<p align="center">
  <em>Desarrollado como Trabajo Fin de Máster (TFM) — calificado como <strong>Excelente</strong>.</em>
  <br/>
  <a href="https://ops-guard-ai-35ac.vercel.app/">Web</a> · <a href="https://github.com/oscaar90/OpsGuard-AI/issues">Issues</a> · <a href="mailto:oscar@oscarai.tech">Contacto</a>
</p>
