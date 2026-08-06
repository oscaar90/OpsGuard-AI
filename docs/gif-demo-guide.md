# Guía: Crear el GIF Demo para OpsGuard-AI

El GIF ideal dura 20-30 segundos y muestra:

```
PR con secreto hardcodeado → GitHub Actions corre → OpsGuard bloquea → Issue abierto
```

---

## Herramientas en Linux (Nobara)

**Opción A — Grabar video y convertir (mejor calidad)**
```bash
sudo dnf install peek         # grabador de pantalla → GIF directo
# o
sudo dnf install ffmpeg       # para convertir mp4 → gif después
```

`peek` es lo más simple: seleccionas el área, grabas, exporta GIF directamente.

**Opción B — Terminal only con asciinema (si el output es solo terminal)**
```bash
sudo dnf install asciinema
asciinema rec demo.cast
# Convierte a GIF
pip install agg
agg demo.cast demo.gif
```

---

## Cómo montar el escenario

1. Crear un repo de prueba `test-opsguard` con OpsGuard instalado
2. Abrir un PR con código que tenga un secreto obvio:

```python
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

3. Grabar la pantalla mientras se abre el PR y corre la Action

---

## Qué grabar exactamente

| Paso | Qué se ve | Duración |
|------|-----------|----------|
| 1 | PR abierto con el código vulnerable visible | 3s |
| 2 | Tab de Actions — job corriendo | 3s |
| 3 | Output del job con `BLOCK` verdict | 5s |
| 4 | Issue generado automáticamente con el informe | 5s |

**Consejo**: Acelera los tiempos de espera del job (tarda ~30s) cortándolos en el video antes de convertir a GIF.

---

## Una vez tengas el GIF

Guárdalo en `docs/assets/demo.gif` y descomenta la sección en el README.md:

```markdown
## See it in Action

![OpsGuard blocking a vulnerable PR](docs/assets/demo.gif)
```

---

## Pendiente

- [ ] Instalar `peek` o `ffmpeg`
- [ ] Crear repo de prueba `test-opsguard`
- [ ] Grabar el GIF
- [ ] Guardarlo en `docs/assets/demo.gif`
- [ ] Descomentar la sección en `README.md`
- [ ] Commit + push + merge PR #78
