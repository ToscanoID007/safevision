# Red: cómo se encuentran la PC y el robot

**Para quién es y cuándo leerlo**
Para quien conecta la PC con el robot por primera vez, o cuando "ayer funcionaba y hoy no
lo encuentra".
Léelo entero una vez; después normalmente basta con la §2 y la §6 (diagnóstico).

---

## 1. El mapa completo

```mermaid
flowchart TB
    subgraph LAN["Red local — Wi-Fi del laboratorio"]
        subgraph PC["PC — Ubuntu"]
            NAV["Navegador"] -->|"127.0.0.1:5000"| DASH["Dashboard Flask<br/>escucha SOLO en localhost"]
        end
        subgraph PI["Robot — Raspberry Pi (yahboom)"]
            RS["Robot Server<br/>0.0.0.0:8091"]
            RC["ROS Master<br/>IP-LAN:11311"]
            SD["Servidor de descarga<br/>0.0.0.0:8090"]
            RS --- RC
        end
        DASH -->|"HTTP :8091<br/>video, mapas, navegacion"| RS
    end
    INT(["Internet"]) -.->|"NUNCA<br/>exponer"| PI
```

| Servicio | Dónde corre | Escucha en | Para qué |
|---|---|---|---|
| **Robot Server** | robot | `0.0.0.0:8091` | API HTTP↔ROS: vídeo, mapas, pose, navegación, misiones |
| **ROS Master** | robot | `<IP-LAN>:11311` | registro de nodos y tópicos ROS |
| Servidor de descarga | robot | `0.0.0.0:8090` | entrega el `.tar.gz` del dashboard |
| **Dashboard** | PC | `127.0.0.1:5000` | interfaz web |

> **Detalle de seguridad bien resuelto:** el dashboard escucha **sólo en `127.0.0.1`**
> (`sf_app_dashboard.py`), así que no es accesible desde otras máquinas de la red.
> Es correcto y no debe cambiarse.

## 2. Uso normal: mDNS (`yahboom.local`)

El robot se anuncia por mDNS/Avahi con el nombre **`yahboom`**, de modo que responde a
`yahboom.local` sin que nadie sepa su IP.

```bash
ping -c 3 yahboom.local
```

Es lo que usa `scripts/robot.env` por defecto, y funciona mientras la PC y el robot estén
en la **misma red local**.

### 2.1 La trampa: el dashboard NO acepta nombres

**CONFIRMADO** (`sf_app_dashboard.py:506-518`): la casilla "IP del robot" valida con
`ipaddress.ip_address()` y acepta **únicamente un IPv4 literal**. Escribir `yahboom.local`
devuelve *"IP inválida"*.

Por eso `./scripts/run_dashboard.sh` resuelve el nombre y te imprime el número exacto:

```
 En la casilla 'IP del robot' escribe:  192.168.1.13
```

### 2.2 Y la IP cambia

El router la asigna por DHCP. **Ya ha cambiado al menos dos veces** en la historia de este
proyecto:

| Dónde aparece | IP | Estado |
|---|---|---|
| Scripts antiguos (`auto_mapeo.sh`, `mapeo_denso.sh`, `api/*`) | `192.168.1.75` | **obsoleta** |
| `backups/start_hybrid_mapping.sh.old` | `192.168.1.69` | **obsoleta** |
| Robot verificado el 2026-09-10 | `192.168.1.13` | vigente ese día |

**Conclusión: no escribas IPs en ningún sitio.** Deja que `run_dashboard.sh` la resuelva,
o fija una reserva DHCP (§3). Las IP de los scripts antiguos son sólo *fallbacks* de
código heredado; ver `docs/security-scan.md` H-8.

## 3. Opción recomendada: reserva DHCP en el router

Más estable que una IP estática en el robot, porque no se rompe al cambiar de red.

1. Consigue la MAC del robot:

```bash
ssh pi@yahboom.local "ip -o link show wlan0 | awk '{print \$17}'"
```

2. En el router: *DHCP* → *Reserva de direcciones* / *Static Lease* → asocia esa MAC a una
   IP fuera del rango dinámico (por ejemplo `192.168.1.50`).
3. Reinicia el robot y comprueba: `ping -c 3 192.168.1.50`
4. Fíjala en la PC:

```bash
echo "ROBOT_HOST=192.168.1.50" > scripts/robot.env
```

**[PENDIENTE: decidir con el profesor si se reserva una IP fija, y anotarla aquí.]**

## 4. Alternativa: IP estática en el robot

Sólo si no hay acceso al router. El robot usa **netplan**.

> ⚠️ Una IP estática mal puesta **te deja sin acceso al robot por red**. Hazlo con teclado
> y pantalla conectados, o teniendo a mano cómo sacar la tarjeta.

```bash
sudo nano /etc/netplan/02-wifi.yaml
```

```yaml
network:
  version: 2
  wifis:
    wlan0:
      dhcp4: no
      addresses: [192.168.1.50/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [192.168.1.1, 8.8.8.8]
      access-points:
        "NOMBRE_DE_LA_RED":
          password: "LA_CONTRASEÑA"
```

```bash
sudo netplan try      # revierte solo a los 120 s si pierdes la conexion
sudo netplan apply
```

> 🔒 Ese fichero contiene la contraseña del Wi-Fi **en claro**. Una copia suya
> (`backups/02-wifi.yaml.bak`) está publicada en GitHub con la PSK real. Ver
> `docs/security-scan.md` H-2: **hay que rotar esa contraseña**.
> **Nunca versiones un netplan con contraseña.**

## 5. Cambiar de red Wi-Fi

Con acceso por SSH o por teclado:

```bash
sudo nmcli dev wifi rescan
sudo nmcli dev wifi list
sudo nmcli dev wifi connect "NOMBRE_DE_LA_RED" --ask
```

`--ask` pide la contraseña de forma interactiva, **sin dejarla en el historial ni en la
lista de procesos**. El script del repositorio `network/wifi_manager.sh:22` la pasa en la
línea de órdenes, lo que la hace visible a cualquier usuario local
(`docs/security-scan.md` H-4): prefiere `--ask`.

Sin acceso por red: conecta teclado y pantalla HDMI al robot, o edita el netplan montando
la microSD en otro equipo.

## 6. Diagnóstico: "no encuentro el robot"

Por orden. No saltes pasos.

### 6.1 ¿Está encendido y en la red?

```bash
ping -c 3 yahboom.local
```

- **Responde** → ve a §6.3.
- **`Name or service not known`** → mDNS no resuelve; §6.2.
- **`Destination Host Unreachable`** → no está en tu red: comprueba que ambos estéis en el
  mismo Wi-Fi (no uno en la red de invitados).

### 6.2 Cuando `yahboom.local` no resuelve

```bash
# ¿Tiene la PC el resolutor mDNS?
systemctl status avahi-daemon
sudo apt install -y avahi-daemon libnss-mdns

# Buscar el robot por descubrimiento
avahi-browse -art | grep -i yahboom

# O barrer la red (ajusta el prefijo al tuyo)
ip route | grep default
sudo apt install -y nmap
nmap -sn 192.168.1.0/24 | grep -B2 -i "raspberry\|yahboom"
```

Causas frecuentes: el punto de acceso tiene activado el *aislamiento de clientes*
(*AP isolation*), o la PC y el robot están en VLAN/bandas distintas.

### 6.3 ¿Responde el Robot Server?

```bash
curl -s --max-time 5 http://<IP>:8091/health | python3 -m json.tool
```

- **Devuelve JSON** → la red está bien. Si algo falla, es del robot:
  `docs/solucion-problemas.md`.
- **`Connection refused`** → el servicio no corre:

```bash
ssh pi@yahboom.local 'systemctl status safevision-robot-server'
```

- **Se queda colgado sin responder** → cortafuegos intermedio, o `ping` funciona pero el
  puerto está bloqueado.

### 6.4 Responde pero `"ok": false`

**Es lo normal recién arrancado.** No es un fallo de red. El robot levanta sólo el ROS
Master y el Robot Server; falta aplicar un perfil de runtime. Ver
`docs/manual-operacion.md` y `docs/estado-actual.md` §1.

## 7. Lo que NO debe exponerse a Internet

> 🔒 **Regla dura. No es una recomendación.**
> Está en `CLAUDE.md` (regla 5) y en el handoff §50 y §64.

| Puerto | Servicio | Riesgo si se expone |
|---|---|---|
| **8091** | Robot Server | **Control total del robot sin contraseña.** `POST /runtime/keyboard` lo mueve; `POST /runtime/profile` enciende motores; `POST /maps/…/delete` borra mapas |
| **11311** | ROS Master | ROS 1 **no tiene autenticación ni cifrado**. Cualquiera puede publicar en `/cmd_vel` y mover el robot |
| 8090 | Descarga | Entrega un paquete de 395 MB a quien lo pida |

**Ningún servicio de SafeVision tiene autenticación.** Se verificó: `git grep` de
`secret_key|auth|login` no devuelve una sola línea en el código del proyecto
(`docs/security-scan.md` H-6). **La frontera de la red es la única frontera de seguridad
que hay.**

Por tanto:

- ❌ **Nunca** abras puertos en el router hacia el robot (*port forwarding*).
- ❌ **Nunca** pongas el robot en la DMZ.
- ❌ Desactiva UPnP en el router si no lo necesitas.
- ✅ Para acceso remoto legítimo, usa **VPN o Tailscale**, y sólo eso.
- ✅ En un laboratorio compartido, considera una red o VLAN separada para los robots.

### 7.1 Acceso remoto correcto: Tailscale

```bash
# En el robot y en la PC
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Ambos quedan en una red privada cifrada. El robot sigue **sin** exponer nada a Internet:
sólo es accesible desde los dispositivos de tu cuenta.

**[PENDIENTE: decidir si se instala Tailscale, y quién administra la cuenta.]**

## 8. Referencia rápida

```bash
# ¿Está vivo?
ping -c 3 yahboom.local

# ¿Qué IP tiene?
getent ahostsv4 yahboom.local | head -1

# ¿Responde el Robot Server?
curl -s http://$(getent ahostsv4 yahboom.local | awk 'NR==1{print $1}'):8091/health \
  | python3 -m json.tool

# Arrancar el dashboard (resuelve la IP solo)
./scripts/run_dashboard.sh
```

## 9. Documentos relacionados

- `docs/instalacion-pc.md` — instalar el dashboard.
- `docs/instalacion-robot.md` — restaurar o reconstruir el robot.
- `docs/solucion-problemas.md` — síntoma → causa → solución.
- `docs/security-scan.md` — credenciales expuestas y qué rotar.
