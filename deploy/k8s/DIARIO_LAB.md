# Diario del lab — OpsGuard-AI sobre k3s

> Lab de una mañana (2026-07-04). Timebox ~4h. Hechos, no prosa. Materia prima
> para el bruto del post (la IA no escribe el post). Un lab que se atasca también
> es post.

## Entorno de partida (antes de tocar nada)

- Máquina: nobara-pc, 8 vCPU, 61 GiB RAM. Docker y k3s ya instalados de antes.
- Homelab ya corriendo en Docker: Grafana + smartctl-exporter (no se toca).

## Bitácora

### 07:59 — Objetivo 1: k3s ya estaba sano, no se instaló hoy
- Hecho: `k3s` activo (systemd) y nodo `nobara-pc` Ready desde hace 91 días.
  Versión v1.34.6+k3s1, un nodo control-plane. Traefik (ingress), local-path
  (storage default), metrics-server y coredns arriba.
- Decisión: NO reinstalar. El objetivo 1 del prompt ("k3s instalado y sano")
  ya estaba cubierto por un clúster previo de Óscar. Se documenta honesto: esta
  mañana no se montó k3s desde cero, se reutilizó el que ya había. Eso no resta
  hands-on a lo que viene (build, manifests, secret, scan), que sí es nuevo.
- Error encontrado: `kubectl` daba `permission denied` sobre
  `/etc/rancher/k3s/k3s.yaml` (0600 root). Además k3s exporta `KUBECONFIG`
  apuntando a ese fichero root a nivel global.
- Cómo se resolvió: copia a `~/.kube/config` con `sudo cp` + `chown oscar` +
  `chmod 600`, y `export KUBECONFIG=$HOME/.kube/config` en cada invocación
  (el KUBECONFIG global de k3s pisa el default, hay que sobreescribirlo).

### 08:00 — Objetivo 2: build de la imagen (en curso)
- Contexto: k3s usa containerd, no el daemon de Docker. Una imagen construida
  con `docker build` NO es visible para k3s por defecto. Hay que exportarla e
  importarla al containerd de k3s (`docker save | k3s ctr images import`).
- Decisión de tag: `opsguard:lab` (imagen local, sin registry). El manifest usará
  `imagePullPolicy: IfNotPresent` para que no intente ir a un registry.
- Hecho: `docker build -t opsguard:lab .` OK. `docker save | sudo k3s ctr images
  import` → imagen visible en containerd (389 MiB). Objetivo 2 cerrado.

### 08:05 — Bug de la imagen: click 8.3.1 rompe el parseo de opciones de typer 0.9.4
- Error encontrado: `opsguard --help` y `opsguard scan --path X` revientan con
  `TypeError: Parameter.make_metavar() missing 1 required positional argument:
  'ctx'`. Es incompatibilidad conocida: el `poetry.lock` fija `click 8.3.1`, y
  typer 0.9.x llama a `make_metavar()` con la firma vieja. Cualquier opción de la
  CLI (--path, --config, --help) queda inservible.
- Impacto real: BAJO para el uso previsto. La GitHub Action invoca `opsguard scan`
  SIN opciones (todo por defecto: path ".", config "opsguard.yml"). Ese camino no
  pasa por el parseo roto y funciona. Se decide NO tocar dependencias hoy (sería
  abrir un frente que el prompt prohíbe: "nada de rediseñar OpsGuard"). Se anota
  como deuda del repo para una sesión aparte (subir typer o pinnear click <8.2).
- Consecuencia de diseño para el lab: como no puedo pasar `--path`, el escaneo se
  hace con cwd = repo y `opsguard scan` a secas. El repo de prueba se construye
  DENTRO del contenedor (evita además el "dubious ownership" de git con volúmenes
  montados de host).

### 08:08 — Cómo dispara Gate 1: hace falta HEAD
- Error encontrado: primer intento de scan devolvía el help de `git diff`.
  Causa: `GitManager.get_staged_files()` hace `git diff HEAD --name-only`; un repo
  recién `git init` sin commit no tiene HEAD → git falla. Gate 1 escanea líneas
  añadidas (`+`) del diff contra HEAD.
- Cómo se resolvió: el script del escaneo commitea una línea base limpia primero y
  DESPUÉS introduce el fichero con las claves AWS. Así hay HEAD y el diff muestra
  el secreto como línea añadida. Validado en local (docker run): Gate 1 caza 2
  violaciones y sale con exit 1.

### 08:12 — Objetivo 3: manifests aplicados
- Hecho: namespace `opsguard`, Secret (imperativo, valor dummy — Gate 1 no usa la
  key), Deployment runner, Service ClusterIP, Ingress Traefik. Runner `Running`,
  readiness OK. Secret cableado por `envFrom` (verificado: la env var aparece en
  el pod).
- Decisión honesta sobre Service+Ingress: OpsGuard NO expone puerto HTTP, es batch.
  Los escribo como práctica de manifiestos CKA pero apuntan a un backend que no
  escucha. Verificado: `curl` al Ingress devuelve **HTTP 502** (Traefik y el
  Service resuelven, no hay proceso en el puerto). No se maquilla: queda escrito
  en los propios manifests y aquí. El primitivo honesto es el Job.

### 08:15 — Objetivo 4: escaneo real DENTRO del clúster
- Hecho: `Job/opsguard-scan` (script vía ConfigMap) corre en el pod, construye el
  repo, mete el PR malicioso y lanza `opsguard scan`. Gate 1 detecta las 2 claves
  AWS → `⛔ PIPELINE BLOCKED`. El pod sale con Error y el Job queda `Failed`: es el
  comportamiento fail-closed correcto (BLOCK = exit≠0), no un fallo del lab.
- Salida visible con `kubectl -n opsguard logs job/opsguard-scan`. Verificación
  real conseguida sin API key (solo detección local determinista).

### 08:16 — Objetivo 5 (stretch, métricas): NO se entra
- Decisión: no se hace y NO es deuda. OpsGuard no tiene endpoint de métricas, y
  añadirlo sería rediseñar la herramienta (frente prohibido). Instrumentar un Job
  batch con Prometheus pide pushgateway o exponer /metrics: eso es el lab 2 de
  observabilidad, con su propio timebox. La zona fuerte de Óscar (Grafana/Prometheus)
  se reserva para cuando haya una superficie que medir.

## Estado final de los 5 objetivos

1. k3s sano + kubectl: ✅ (pre-existente, no montado hoy — honesto).
2. Imagen construida e importada a k3s: ✅.
3. Deployment+Service+Ingress+Secret: ✅ aplicados. Secret real (envFrom).
   Service/Ingress funcionalmente vacíos (502): OpsGuard no tiene HTTP. Documentado.
4. Escaneo real dentro del clúster: ✅ (Job, Gate 1 BLOCK, logs visibles).
5. Métricas/Grafana (stretch): ⛔ no entra — es el lab 2, no deuda.

## La tensión central (materia para el post y para el veredicto CV)

El lab funciona, pero revela lo que ya olía: OpsGuard encaja en K8s como **Job/CronJob
disparado por CI**, no como servicio con Deployment+Service+Ingress. El Secret y el
Job son defendibles al 100%. El Service y el Ingress son andamiaje pedagógico: un 502
honesto. Reencuadrar OpsGuard como "servicio operado en Kubernetes" es forzar; como
"gate batch contenedorizado y desplegado como Job en k8s, con la API key en Secret" es
verdad y se sostiene en entrevista.

## Dos pasos que son de Óscar (no los hace la IA)

1. Escribir el BRUTO del post con su voz (esto es materia prima, no el post). El
   borrador sale luego de `/linkedin-editor` con texto suyo.
2. Decidir sobre el CV: el veredicto de abajo es una PROPUESTA. El CV no se toca sin
   pasar por `_meta/cv_maestro/AGENT.md` e instrucción explícita en otra sesión.
