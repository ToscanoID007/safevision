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
y te dice en qué IP está y qué tiene encendido. Luego abre `http://127.0.0.1:5000`:
el dashboard ya está conectado, **no hay que escribir ninguna IP**.

Si alguna vez la necesitas escribir: en la red propia del robot es **siempre `10.42.0.1`**;
en cualquier otra red usa **`yahboom.local`**.

**Ayuda dentro del dashboard.** El botón **Tutorial** de la portada recorre todo esto paso a
paso, resaltando cada parte de la pantalla. Y al pasar el ratón sobre cualquier tarjeta o
enlace del menú aparece qué hace, cuándo usarlo y qué necesitas antes (en el móvil, el
primer toque muestra la ficha y el segundo abre la sección).

**Las guías dentro del dashboard.** El botón **Guía**, abajo a la derecha en todas las
páginas, abre esta guía, el manual y las seis prácticas en un panel al lado. La página sigue
funcionando mientras lees, y el panel recuerda qué documento y qué parte estabas leyendo al
cambiar de página. Funciona sin internet.

**Sólo la primera vez en una laptop**, instala el entorno (tarda unos minutos):

```bash
PYTHON_BIN=python3.8 ./scripts/install_dashboard.sh    # cualquier python3 >= 3.8
```

---

## 3. Dejar el robot listo para moverse

Al encender, el robot **no se mueve**: sólo arranca lo mínimo. Para operarlo:

1. En el dashboard entra a **Pilotada**. Comprueba que el control está en **Mando**.
2. **Sólo manejar:** pulsa **Modo Libre**.
   **Con mapa:** elige el mapa en la lista de la derecha (*Localización · Mapa*) y pulsa
   **Misión Pilotada**.
3. No hay botón «Aplicar»: **ese clic ya activa el modo**. Espera hasta 2 minutos; el cuadro
   *Actividad* muestra cada parte que arranca y la insignia de arriba cambia al terminar.

Ya puedes moverlo con el mando. Si va demasiado rápido, baja **Velocidad del mando** en la
misma página (30-40 % va bien para mapear). **Para pararlo: suelta el mando.** Se detiene en medio
segundo, también si se corta el Wi-Fi o cierras el dashboard.

La página **Nodos** muestra qué parte está encendida y deja encender o apagar cada una.

---

## 4. Enseñarle al robot una red nueva

**Desde el dashboard** (página **Wi-Fi**, tarjeta 08 de la portada):

1. Si el robot no conoce ninguna red del lugar, conecta la laptop a **`SafeVision-Robot`**
   y arranca el dashboard. Si ya estás en la misma red que el robot, sáltate este paso.
2. Abre **Wi-Fi**. Verás las redes que ve el robot, con su banda.
   **El robot sólo usa redes de 2.4 GHz:** las de 5 GHz salen en gris.
3. Pulsa **Elegir** en la red, escribe su contraseña y deja marcado **Conectar ahora**.
4. Tu laptop perderá la conexión con el robot. Conéctala a esa misma red y vuelve a la
   página: encuentra al robot sola, en menos de un minuto.

Si la contraseña era incorrecta, el robot vuelve a crear `SafeVision-Robot` y la página te
lo dice. La red queda guardada: la próxima vez que el robot la vea al encender, se conecta solo.

> En su red propia el robot no puede buscar redes sin desconectarte, así que muestra
> **la lista que vio al encender**. Si la red no aparece, usa «¿No aparece? Escribe el nombre».
> No sirven las redes que piden iniciar sesión en una página web ni las que piden usuario.

**Por consola** (si no tienes el dashboard a mano):

```bash
ssh pi@10.42.0.1
sudo nmcli connection add type wifi ifname wlan0 con-name "NOMBRE" ssid "NOMBRE" \
     802-11-wireless.band bg wifi-sec.key-mgmt wpa-psk wifi-sec.psk "CLAVE" \
     connection.autoconnect-priority 10
sudo reboot
```

Para borrar una red guardada: botón **Olvidar** en la página, o
`sudo nmcli connection delete "NOMBRE"`.

---

## 5. Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `run_dashboard.sh` no encuentra el robot | ¿Pasaron 2 minutos? ¿La laptop está en la misma red? Si no, busca `SafeVision-Robot` |
| No aparece ni la red del robot | Conecta un cable Ethernet entre robot y router, o monitor y teclado a la Raspberry |
| `yahboom.local` no funciona pero la IP sí | En Ubuntu falta mDNS: `sudo apt install -y avahi-daemon libnss-mdns`. **En WSL** es normal: Linux no recibe mDNS; `run_dashboard.sh` y el dashboard le preguntan el nombre a Windows. Para `ssh` usa la IP |
| "Robot no conectado" | La laptop no está en la misma red que el robot. En su propia red el robot siempre es `10.42.0.1` |
| `No module named 'requests'` | Reinstala el entorno: paso 2, la línea de la primera vez, tras `rm -rf misiones/pilotada/dashboard_src/.venv` |
| El robot pita sin parar | Batería baja: apágalo bien y cárgalo |
| La página Wi-Fi no existe o da error | El robot tiene una versión anterior: `./scripts/robot_actualizar.sh` (o con su IP) |
| Activar el modo falla | Pulsa otra vez el botón del modo; el gestor reconstruye lo que falte. Si sigue, mira la página **Nodos** |
| Pulsas Misión Pilotada y no pasa nada | Falta elegir el mapa en la lista de la derecha; el cuadro *Actividad* lo avisa |
| Mapear tarda en arrancar | Normal la primera vez: *Iniciar mapeo* pone antes el robot en Misión Pilotada con un mapa de retorno (hasta 2 minutos) |

Más casos en `solucion-problemas.md`.
