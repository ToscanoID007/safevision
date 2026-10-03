# Guía rápida — lo básico en una página

Para quien tiene el robot delante por primera vez. Si algo de aquí no basta, el detalle
está en `manual-operacion.md` y `red.md`.

---

## 0. La idea en 30 segundos

Hay tres piezas: **el robot**, **tu laptop** y **una red Wi-Fi que los une**.
El dashboard corre en tu laptop y habla con el robot por esa red.

El robot elige la red solo al encender:

| Si al encender el robot… | …entonces el robot | Y tú conectas la laptop a |
|---|---|---|
| ve una red que ya conoce | se conecta a ella | esa misma red |
| no ve ninguna conocida | **crea su propia red** `SafeVision-Robot` y queda en `10.42.0.1` | `SafeVision-Robot` |
| tiene el cable Ethernet puesto | además responde por cable | el mismo cable/switch |

Redes que el robot ya conoce: `Mega_2.4G_38FE`, `INFINITUMEB8A`, `Red_local_luis`,
`Y_Lab_de_Control`. La clave de `SafeVision-Robot` te la da quien configuró el robot;
no está en el repositorio.

---

## 1. Encender y apagar

**Encender:** interruptor del robot y espera **2 minutos**. Si a los 2 minutos no aparece
en tu red, busca la red `SafeVision-Robot` en la laptop.

**Apagar** (nunca cortes la corriente sin esto, se daña la microSD):

```bash
ssh pi@yahboom.local 'sudo shutdown -h now'      # o pi@10.42.0.1 en su propia red
```

Espera a que se apague la luz verde de la Raspberry y entonces apaga el interruptor.
**Si el robot pita sin parar es batería baja:** apágalo así y ponlo a cargar.

---

## 2. Abrir el dashboard

En la laptop, desde la carpeta del repositorio:

```bash
./scripts/run_dashboard.sh
```

El script **encuentra solo al robot** (por nombre, por `10.42.0.1` o buscando en la red)
y te dice en qué IP está y qué tiene encendido. Luego abre `http://127.0.0.1:5000`.

**Sólo la primera vez en una laptop**, instala el entorno (tarda unos minutos):

```bash
PYTHON_BIN=python3.8 ./scripts/install_dashboard.sh    # cualquier python3 >= 3.8
```

---

## 3. Dejar el robot listo para moverse

Al encender, el robot **no se mueve**: sólo arranca lo mínimo. Para operarlo:

1. En el dashboard entra a **Pilotada**.
2. Elige el mapa (`HAB2` o el tuyo) y el control (**mando**).
3. Pulsa **Aplicar** y espera hasta 2 minutos. El registro muestra cada parte que arranca.

Ya puedes moverlo con el mando. **Para pararlo: suelta el mando.** Se detiene en medio
segundo, también si se corta el Wi-Fi o cierras el dashboard.

La página **Nodos** muestra qué parte está encendida y deja encender o apagar cada una.

---

## 4. Enseñarle al robot una red nueva

Sirve en cualquier sitio, aunque el robot no conozca ninguna red:

1. Enciende el robot y espera 2 minutos. Conecta la laptop a **`SafeVision-Robot`**.
2. Entra al robot:
   ```bash
   ssh pi@10.42.0.1
   ```
3. Guarda la red nueva (cambia `NOMBRE` y `CLAVE`, respetando las comillas):
   ```bash
   sudo nmcli connection add type wifi ifname wlan0 con-name "NOMBRE" ssid "NOMBRE" \
        wifi-sec.key-mgmt wpa-psk wifi-sec.psk "CLAVE" connection.autoconnect-priority 10
   sudo reboot
   ```
4. Conecta la laptop a la red nueva y, a los 2 minutos, `./scripts/run_dashboard.sh`.

Si te equivocaste de clave no pasa nada: el robot no logra conectarse, vuelve a crear
`SafeVision-Robot` y repites desde el paso 1. Para borrar una red guardada:
`sudo nmcli connection delete "NOMBRE"`.

> Este método guarda la red **sin buscarla**, que es lo que hace falta: mientras el robot
> crea su propia red no puede buscar otras. No sirve con redes que piden iniciar sesión
> en una página web (redes de invitados, algunas institucionales).

---

## 5. Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `run_dashboard.sh` no encuentra el robot | ¿Pasaron 2 minutos? ¿La laptop está en la misma red? Si no, busca `SafeVision-Robot` |
| No aparece ni la red del robot | Conecta un cable Ethernet entre robot y router, o monitor y teclado a la Raspberry |
| "Robot no conectado" en *Mapear* o *Mapas* | Entra antes a **Pilotada** o **Nodos** |
| `No module named 'requests'` | Reinstala el entorno: paso 2, la línea de la primera vez, tras `rm -rf misiones/pilotada/dashboard_src/.venv` |
| El robot pita sin parar | Batería baja: apágalo bien y cárgalo |
| Aplicar el perfil falla | Pulsa **Aplicar** otra vez; el gestor reconstruye lo que falte. Si sigue, mira la página **Nodos** |

Más casos en `solucion-problemas.md`.
