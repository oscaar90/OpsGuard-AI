# Role
Actúa como Senior Python DevOps Engineer.

# Context
Estamos construyendo 'OpsGuard-AI', una GitHub Action dockerizada.
El entorno Docker ya funciona. Ahora necesitamos implementar la lógica de lectura de cambios (Git Diff).

# Task 1: Module src/ingest.py
Implementa una clase `GitManager` que encapsule la librería `gitpython`.

Requisitos funcionales:
1. Constructor `__init__`: Debe aceptar el path del repositorio.
2. Método `is_ci()`: Debe devolver True si la variable de entorno `GITHUB_ACTIONS` está presente.
3. Método `get_diff()`:
   - Estrategia Local: Si `is_ci()` es False, ejecuta un diff contra HEAD (`git diff HEAD`). Esto es para probar cambios no commiteados en desarrollo local.
   - Estrategia CI (GitHub Actions):
     - Leer la variable `GITHUB_EVENT_PATH`.
     - Parsear el JSON del evento.
     - Extraer `pull_request.base.sha` y `pull_request.head.sha`.
     - Ejecutar el diff entre esos dos hashes.
   - Manejo de Errores: Capturar excepciones de `gitpython` y lanzar errores propios o mensajes claros.

# Task 2: Update src/main.py
Actualiza el CLI existente para usar este nuevo módulo.
1. Importa `GitManager` de `src.ingest`.
2. Añade un comando `scan` al objeto `app` de Typer.
3. El comando `scan` debe instanciar `GitManager` y mostrar el resultado de `get_diff()` por stdout.

# Output Format
Proporciona únicamente el código fuente completo para:
1. `src/ingest.py`
2. `src/main.py`
