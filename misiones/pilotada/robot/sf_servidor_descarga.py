#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket


PORT = 8090

PAQUETE = Path(
    "/home/pi/robot_custom/misiones/pilotada/payload/"
    "SafeVision_Dashboard_Ubuntu18_x86_64.tar.gz"
)


def obtener_ip():
    try:
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:
        return "127.0.0.1"


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":

            if PAQUETE.exists():
                estado = """
                <p>Dashboard disponible.</p>

                <a href="/download">
                    Descargar SafeVision Dashboard
                </a>
                """

            else:
                estado = """
                <p>
                    Dashboard no disponible.
                </p>
                """

            html = """
<!doctype html>

<html lang="es">

<head>

<meta charset="utf-8">

<title>SafeVision Dashboard</title>

<style>

body {
    background: #080d14;
    color: #edf5ff;
    font-family: sans-serif;

    max-width: 650px;

    margin: 80px auto;
    padding: 20px;
}

.box {
    background: #101822;

    border: 1px solid #263548;
    border-radius: 12px;

    padding: 30px;
}

h1 {
    margin-top: 0;
}

p {
    color: #aebed0;
}

a {
    display: inline-block;

    margin-top: 15px;

    padding: 12px 18px;

    background: #3b82f6;
    color: white;

    text-decoration: none;

    border-radius: 7px;
}

</style>

</head>

<body>

<div class="box">

<h1>SafeVision</h1>

<h2>Dashboard Ubuntu 18.04 x86_64</h2>

%s

</div>

</body>

</html>
""" % estado

            datos = html.encode("utf-8")

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(datos))
            )

            self.end_headers()

            self.wfile.write(datos)

            return


        if self.path == "/download":

            if not PAQUETE.exists():

                self.send_error(
                    404,
                    "Dashboard no disponible"
                )

                return


            tamaño = PAQUETE.stat().st_size


            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/gzip"
            )

            self.send_header(
                "Content-Length",
                str(tamaño)
            )

            self.send_header(
                "Content-Disposition",
                'attachment; filename="{}"'.format(
                    PAQUETE.name
                )
            )

            self.end_headers()


            with PAQUETE.open("rb") as archivo:

                while True:

                    bloque = archivo.read(
                        1024 * 1024
                    )

                    if not bloque:
                        break

                    self.wfile.write(
                        bloque
                    )

            return


        self.send_error(404)


    def log_message(
        self,
        format,
        *args
    ):
        pass


def main():

    if not PAQUETE.exists():

        print("")
        print("ERROR: paquete no encontrado:")
        print(PAQUETE)
        print("")

        return 1


    ip = obtener_ip()


    print("")
    print("=========================================================")
    print("       SAFEVISION - DESCARGAR DASHBOARD")
    print("=========================================================")
    print("")
    print(" Archivo:")
    print(" {}".format(PAQUETE.name))
    print("")
    print(" Tamaño: {:.1f} MB".format(
        PAQUETE.stat().st_size / 1024 / 1024
    ))
    print("")
    print(" Abra en la computadora:")
    print("")
    print(" http://{}:{}".format(
        ip,
        PORT
    ))
    print("")
    print(" Ctrl+C para regresar.")
    print("")
    print("=========================================================")


    servidor = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        Handler
    )


    try:
        servidor.serve_forever()

    except KeyboardInterrupt:
        pass

    finally:
        servidor.server_close()


    return 0


if __name__ == "__main__":
    raise SystemExit(main())
