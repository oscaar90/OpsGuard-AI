# OpsGuard-AI - Shooting Range

> Colección de archivos intencionalmente vulnerables para demostrar las capacidades de detección de OpsGuard-AI.

Estos ficheros están excluidos del análisis automático de OpsGuard (ver `.opsguardignore`) porque contienen vulnerabilidades **a propósito**. Su función es doble:

1. **Demostración en vivo** - el profesor puede copiar cualquier fichero a otra ruta, hacer commit y abrir una PR; OpsGuard bloqueará el pipeline.
2. **Base de los tests unitarios** - `tests/test_security.py` los usa programáticamente para validar el motor de detección.

---

## Inventario de Fixtures

| Fichero | Vulnerabilidad | Detectado por | Gate |
|---------|---------------|---------------|------|
| `vulnerable_app/aws_creds.env` | AWS Access Key hardcodeada (`AKIA…`) | Regex | **Gate 1** |
| `vulnerable_app/legacy_login.py` | SQL Injection (f-string sin sanitizar) | IA semántica | **Gate 2** |
| `vulnerable_app/auth_middleware.py` | Backdoor de developer (`X-DEBUG-MODE`) | IA semántica | **Gate 2** |
| `vulnerable_app/config.php` | Password y API Key hardcodeadas (PHP) | IA semántica | **Gate 2** |
| `vulnerable_app/supply_chain_attack.py` | Supply-Chain Typosquatting (`ghrc.io` → `ghcr.io`) | IA semántica | **Gate 2** |
| `vulnerable_app/ai_agent_commit.py` | Agente de IA autonomo: credenciales + SQL Injection + auth bypass | Ambos gates | **Gate 1 + Gate 2** |

> **Nota de diseño:** `legacy_login.py`, `auth_middleware.py` y `config.php` pasan deliberadamente el Gate 1 (regex). Esto valida que el sistema no produce falsos positivos en vulnerabilidades semánticas y que el Gate 2 (IA) es el responsable de razonar sobre lógica de negocio y contexto.
>
> **`ai_agent_commit.py`** es el fixture de nueva generacion: simula un agente de IA autonomo (Copilot Workspace, Cursor Agent, Devin) que introduce multiples vulnerabilidades en un mismo commit. Demuestra que OpsGuard actua como red de seguridad ante AI-generated code comprometido o con alucinaciones inseguras.

---

## Demo Manual - Instrucciones para el Evaluador

Siga estos pasos para ver OpsGuard en acción bloqueando un commit vulnerable en tiempo real.

### Requisitos previos
```bash
git clone https://github.com/oscaar90/OpsGuard-AI.git
cd OpsGuard-AI
poetry install
cp .env.example .env
# Añadir OPENROUTER_API_KEY en .env
```

### Paso 1 - Elija un fixture

| Si quiere ver… | Use este fichero |
|----------------|-----------------|
| Bloqueo inmediato por regex (Gate 1) | `aws_creds.env` |
| Bloqueo por IA - SQL Injection (Gate 2) | `legacy_login.py` |
| Bloqueo por IA - Backdoor (Gate 2) | `auth_middleware.py` |

### Paso 2 - Copie el fichero a una ruta analizada

```bash
# Ejemplo con el fichero de credenciales AWS
cp tests/fixtures/vulnerable_app/aws_creds.env src/aws_creds.env
```

### Paso 3 - Añada y commitee el cambio

```bash
git checkout -b demo/shooting-range
git add src/aws_creds.env
git commit -m "test: add config file"
git push origin demo/shooting-range
```

### Paso 4 - Abra una Pull Request

Abra la PR desde GitHub. El workflow `opsguard.yml` se activará automáticamente y **bloqueará el merge** con una salida similar a:

```
🛡️ OpsGuard-AI - Security Gate Active

🚨 DETECTED 1 STATIC VIOLATIONS:
┌──────────────────┬──────┐
│ Type             │ File │
├──────────────────┼──────┤
│ [AWS Access Key] │ Diff │
└──────────────────┴──────┘

⛔ PIPELINE BLOCKED: SECURITY VIOLATION DETECTED
```

### Paso 5 - Limpieza

```bash
git checkout main
git branch -D demo/shooting-range
git push origin --delete demo/shooting-range
rm src/aws_creds.env
```

---

## Validación Automática (pytest)

Los mismos fixtures son utilizados por la suite de tests unitarios para validar el motor de forma programática y reproducible:

```bash
poetry run pytest tests/test_security.py -v
```

Salida esperada:

```
tests/test_security.py::TestSecurityPolicyLoading::test_loads_real_config_successfully PASSED
tests/test_security.py::TestSecurityPolicyLoading::test_raises_on_missing_config_file PASSED
tests/test_security.py::TestGate1SecretDetection::test_aws_access_key_triggers_violation PASSED
tests/test_security.py::TestGate1DoesNotOverreach::test_sql_injection_passes_gate1 PASSED
tests/test_security.py::TestGate1DoesNotOverreach::test_logic_backdoor_passes_gate1 PASSED
tests/test_security.py::TestDiffBehavior::test_deleted_lines_are_not_flagged PASSED
...
```
