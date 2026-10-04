# Reglas `udev` del robot

Copia exacta de `/etc/udev/rules.d/` del robot, tomada el 2026-10-03. Son material del
fabricante Yahboom (y de Orbbec, la cámara Astra).

| Archivo | Qué hace | ¿Lo usa SafeVision? |
|---|---|---|
| `rplidar.rules` | Crea `/dev/rplidar` (LiDAR, chip CP210x `10c4:ea60`) y `/dev/myserial` (placa del chasis, chip CH340 `1a86:7523`) | **Sí, imprescindible** |
| `56-orbbec-usb.rules` | Permisos y nombres para la cámara de profundidad Astra | No (la RGB-D no alimenta la navegación) |
| `speech.rules` | Todo comentado; restos del módulo de voz de Yahboom | No |

Los nombres fijos importan porque el orden de los puertos USB cambia: el 2026-10-03 el
robot tenía `/dev/myserial -> ttyUSB0` y `/dev/rplidar -> ttyUSB1`, al revés de lo que se
había anotado antes, y todo funcionaba igual gracias a estas reglas.

**Ojo:** las reglas reconocen los dispositivos por el modelo del chip USB, no por el puerto.
Si se conecta otro adaptador con un chip CH340 (`1a86:7523`), también recibirá el nombre
`myserial` y uno de los dos fallará.

Para instalarlas en un robot reconstruido:

```bash
sudo cp rplidar.rules 56-orbbec-usb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/rplidar /dev/myserial
```
