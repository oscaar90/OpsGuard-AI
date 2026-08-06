# AGENTS.md

## Rol

`OpsGuard-AI` es un producto tecnico real orientado a seguridad en pull requests de GitHub Actions.

## Objetivo

Mantener una herramienta creible, util y defendible tecnicamente:

- deteccion local de secretos primero
- revision semantica de AppSec despues
- coste por analisis controlado
- comportamiento fail-closed

## Reglas

- Haz solo lo pedido y no abras frentes laterales sin justificacion.
- Antes de cambiar arquitectura, revisa `docs/adr/`.
- Prioriza coherencia entre codigo, workflows, README y ADRs.
- No simplifiques la propuesta de valor con claims inflados.
- No introduzcas secretos, credenciales o artefactos temporales en el repo.
- Si cambias comportamiento relevante, ejecuta la validacion minima del area tocada.

## Fuentes De Verdad

- `README.md`: propuesta de valor y flujo principal
- `docs/adr/`: decisiones arquitectonicas
- `.github/workflows/`: integracion real
- `src/`: implementacion
- `tests/`: validacion automatizada
