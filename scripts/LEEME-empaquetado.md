# Empaquetado del dashboard para distribución

**Para quién es y cuándo leerlo**
Para quien necesite generar el `.tar.gz` autocontenido del dashboard, el que el robot sirve
en el puerto 8090 para PCs que no quieran instalar dependencias.
No hace falta para el uso normal: para eso está `scripts/install_dashboard.sh`.

---

## Qué es `SafeVision.spec`

Es la receta de **PyInstaller** con la que se generó
`misiones/pilotada/payload/SafeVision_Dashboard_Ubuntu18_x86_64.tar.gz` (395 MB, del 8 de
agosto de 2026), que sigue en el robot.

Se versiona porque **era el único registro de cómo se construye ese paquete** y vivía sin
control de versiones en `~/SafeVision_Dashboard_dev/`.

Lo relevante de la receta:

- punto de entrada `sf_app_dashboard.py`;
- empaqueta `templates/` y `static/` como datos;
- usa `collect_all('ultralytics')`, que arrastra PyTorch entero — de ahí los 395 MB.

## Cómo regenerarlo

Debe hacerse **en la misma distribución de destino** (Ubuntu 18.04 x86_64 en el paquete
actual): PyInstaller no compila para otras plataformas.

```bash
cd misiones/pilotada/dashboard_src
source .venv/bin/activate
pip install pyinstaller
cp ../../../scripts/SafeVision.spec .
pyinstaller SafeVision.spec
# el resultado queda en dist/SafeVision/
tar czf SafeVision_Dashboard_Ubuntu18_x86_64.tar.gz -C dist SafeVision
```

## Avisos

> ⚠️ **El paquete que hay en el robot está desactualizado.** Es del 8 de agosto, anterior a
> todo el desarrollo del frontend de los días 19 y 20: **no incluye la página `/pilotada`**
> ni los controles de perfil de runtime.

> ⚠️ **Antes de distribuirlo, revisa `docs/security-scan.md`.** Un paquete generado a partir
> de un árbol con credenciales embebidas las distribuye también.

**[PENDIENTE: decidir si se regenera el paquete con el dashboard actual o se retira del
robot para no confundir. Ocupa 395 MB de la tarjeta.]**

## Documentos relacionados

- `docs/instalacion-pc.md` §9 — cuándo usar el paquete y cuándo no.
- `docs/estado-actual.md` §7 — dónde está y qué tamaño tiene.
