#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import threading
import time

import cv2
from ultralytics import YOLO


class MotorInferencia:
    def __init__(self):
        self.lock = threading.RLock()

        self.modelo = None
        self.modelo_path = None
        self.json_path = None

        self.metadata = {}
        self.clases = []

        self.confianza = 0.50


    def cargar_modelo(self, modelo_path, json_path=None):
        try:
            print(
                "[IA] Cargando modelo: {}".format(
                    modelo_path
                )
            )

            nuevo_modelo = YOLO(
                modelo_path
            )

            metadata = {}
            clases = []


            # ---------------------------------------------
            # JSON OPCIONAL
            # ---------------------------------------------

            if json_path and os.path.isfile(
                json_path
            ):
                with open(
                    json_path,
                    "r",
                    encoding="utf-8"
                ) as archivo:
                    metadata = json.load(
                        archivo
                    )

                clases_json = metadata.get(
                    "clases"
                )

                if isinstance(
                    clases_json,
                    list
                ):
                    clases = [
                        str(nombre)
                        for nombre in clases_json
                    ]


            # ---------------------------------------------
            # SI NO HAY CLASES EN JSON, USAR LAS DEL .PT
            # ---------------------------------------------

            if not clases:
                nombres = getattr(
                    nuevo_modelo,
                    "names",
                    {}
                )

                if isinstance(
                    nombres,
                    dict
                ):
                    clases = [
                        str(nombres[k])
                        for k in sorted(
                            nombres.keys()
                        )
                    ]

                elif isinstance(
                    nombres,
                    list
                ):
                    clases = [
                        str(x)
                        for x in nombres
                    ]


            with self.lock:
                self.modelo = nuevo_modelo

                self.modelo_path = str(
                    modelo_path
                )

                self.json_path = (
                    str(json_path)
                    if json_path
                    else None
                )

                self.metadata = metadata
                self.clases = clases


            print(
                "[IA] Modelo cargado."
            )

            print(
                "[IA] Clases: {}".format(
                    len(clases)
                )
            )

            return True, None


        except Exception as exc:
            print(
                "[IA] Error: {}".format(
                    exc
                )
            )

            return False, str(exc)


    def set_confianza(self, valor):
        try:
            valor = float(
                valor
            )

        except Exception:
            return False

        valor = max(
            0.01,
            min(
                0.99,
                valor
            )
        )

        with self.lock:
            self.confianza = valor

        return True


    def get_info(self):
        with self.lock:
            metadata = dict(
                self.metadata
            )

            return {
                "loaded": (
                    self.modelo is not None
                ),

                "model": (
                    os.path.basename(
                        self.modelo_path
                    )
                    if self.modelo_path
                    else None
                ),

                "json": (
                    os.path.basename(
                        self.json_path
                    )
                    if self.json_path
                    else None
                ),

                "confidence": (
                    self.confianza
                ),

                "classes": list(
                    self.clases
                ),

                "metadata": metadata
            }


    def procesar_frame(self, frame):
        with self.lock:
            modelo = self.modelo
            confianza = self.confianza
            clases = list(
                self.clases
            )

        if modelo is None:
            return frame


        try:
            resultados = modelo(
                frame,
                conf=confianza,
                verbose=False
            )

            if not resultados:
                return frame

            resultado = resultados[0]


            # ---------------------------------------------
            # NOMBRES DEL JSON, SI EXISTEN
            # ---------------------------------------------

            if clases:
                try:
                    resultado.names = {
                        i: nombre
                        for i, nombre
                        in enumerate(
                            clases
                        )
                    }

                except Exception:
                    pass


            return resultado.plot()


        except Exception as exc:
            print(
                "[IA] Error de inferencia: {}".format(
                    exc
                )
            )

            return frame


    def generar_stream(self, stream_url):
        cap = None


        while True:
            try:
                if (
                    cap is None
                    or
                    not cap.isOpened()
                ):
                    if cap is not None:
                        cap.release()

                    print(
                        "[VIDEO] Conectando a {}".format(
                            stream_url
                        )
                    )

                    cap = cv2.VideoCapture(
                        stream_url
                    )

                    if not cap.isOpened():
                        time.sleep(
                            0.5
                        )

                        continue


                ok, frame = cap.read()

                if not ok:
                    cap.release()

                    cap = None

                    time.sleep(
                        0.25
                    )

                    continue


                frame = self.procesar_frame(
                    frame
                )


                correcto, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [
                        int(
                            cv2.IMWRITE_JPEG_QUALITY
                        ),
                        80
                    ]
                )

                if not correcto:
                    continue


                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    +
                    buffer.tobytes()
                    +
                    b"\r\n"
                )


            except GeneratorExit:
                break


            except Exception as exc:
                print(
                    "[VIDEO] Error: {}".format(
                        exc
                    )
                )

                if cap is not None:
                    cap.release()

                    cap = None

                time.sleep(
                    0.5
                )


        if cap is not None:
            cap.release()
