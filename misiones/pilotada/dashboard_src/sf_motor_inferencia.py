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

        # Índices de clase. Preservan IDs YOLO.
        self.clases_suspendidas = set()
        self.clases_eliminadas = set()

        self.model_class_count = 0

        self.confianza = 0.50

        # Telemetría ligera.
        self.inference_ms = None
        self.inference_fps = None
        self.stream_fps = None
        self._last_stream_frame_at = None


    @staticmethod
    def _normalizar_indices(value):
        if not isinstance(value, list):
            return set()

        result = set()

        for item in value:
            try:
                index = int(item)
            except Exception:
                continue

            if index >= 0:
                result.add(index)

        return result


    @staticmethod
    def _smooth(previous, current, alpha=0.22):
        if previous is None:
            return float(current)

        return (
            (1.0 - alpha) * float(previous)
            +
            alpha * float(current)
        )


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
            suspendidas = set()
            eliminadas = set()

            nombres_modelo = getattr(
                nuevo_modelo,
                "names",
                {}
            )

            if isinstance(nombres_modelo, dict):
                model_class_count = len(
                    nombres_modelo
                )
            elif isinstance(nombres_modelo, list):
                model_class_count = len(
                    nombres_modelo
                )
            else:
                model_class_count = 0


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

                if not isinstance(metadata, dict):
                    metadata = {}

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

                suspendidas = self._normalizar_indices(
                    metadata.get(
                        "clases_suspendidas"
                    )
                )

                eliminadas = self._normalizar_indices(
                    metadata.get(
                        "clases_eliminadas"
                    )
                )


            # ---------------------------------------------
            # SI NO HAY CLASES EN JSON, USAR LAS DEL .PT
            # ---------------------------------------------

            if not clases:
                if isinstance(
                    nombres_modelo,
                    dict
                ):
                    clases = [
                        str(
                            nombres_modelo[k]
                        )
                        for k in sorted(
                            nombres_modelo.keys()
                        )
                    ]

                elif isinstance(
                    nombres_modelo,
                    list
                ):
                    clases = [
                        str(x)
                        for x in nombres_modelo
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

                self.clases_suspendidas = (
                    suspendidas
                )

                self.clases_eliminadas = (
                    eliminadas
                )

                self.model_class_count = (
                    model_class_count
                )

                self.inference_ms = None
                self.inference_fps = None


            print(
                "[IA] Modelo cargado."
            )

            print(
                "[IA] Clases metadata: {}".format(
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


    def get_stats(self):
        with self.lock:
            return {
                "stream_fps": (
                    round(
                        self.stream_fps,
                        2
                    )
                    if self.stream_fps is not None
                    else None
                ),

                "inference_fps": (
                    round(
                        self.inference_fps,
                        2
                    )
                    if self.inference_fps is not None
                    else None
                ),

                "inference_ms": (
                    round(
                        self.inference_ms,
                        2
                    )
                    if self.inference_ms is not None
                    else None
                )
            }


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

                "suspended_classes": sorted(
                    self.clases_suspendidas
                ),

                "deleted_classes": sorted(
                    self.clases_eliminadas
                ),

                "model_class_count": (
                    self.model_class_count
                ),

                "metadata": metadata,

                "stats": self.get_stats()
            }


    def procesar_frame(self, frame):
        with self.lock:
            modelo = self.modelo
            confianza = self.confianza
            clases = list(
                self.clases
            )
            suspendidas = set(
                self.clases_suspendidas
            )
            eliminadas = set(
                self.clases_eliminadas
            )
            model_class_count = int(
                self.model_class_count
                or
                0
            )

        if modelo is None:
            return frame


        blocked = (
            suspendidas
            |
            eliminadas
        )

        kwargs = {
            "conf": confianza,
            "verbose": False
        }

        if (
            blocked
            and
            model_class_count > 0
        ):
            active_ids = [
                index
                for index in range(
                    model_class_count
                )
                if index not in blocked
            ]

            # Todas las clases reales están suspendidas/eliminadas.
            if not active_ids:
                return frame

            kwargs[
                "classes"
            ] = active_ids


        started = time.perf_counter()

        try:
            resultados = modelo(
                frame,
                **kwargs
            )

            elapsed_ms = (
                time.perf_counter()
                -
                started
            ) * 1000.0

            instantaneous_fps = (
                1000.0 / elapsed_ms
                if elapsed_ms > 0
                else None
            )

            with self.lock:
                self.inference_ms = (
                    self._smooth(
                        self.inference_ms,
                        elapsed_ms
                    )
                )

                if instantaneous_fps is not None:
                    self.inference_fps = (
                        self._smooth(
                            self.inference_fps,
                            instantaneous_fps
                        )
                    )

            if not resultados:
                return frame

            resultado = resultados[0]


            # ---------------------------------------------
            # NOMBRES DEL JSON SIN ROMPER IDS DEL MODELO
            # ---------------------------------------------

            if clases:
                try:
                    original = getattr(
                        resultado,
                        "names",
                        {}
                    )

                    if isinstance(
                        original,
                        dict
                    ):
                        names = dict(
                            original
                        )
                    else:
                        names = {}

                    for index, nombre in enumerate(
                        clases
                    ):
                        if (
                            model_class_count <= 0
                            or
                            index < model_class_count
                        ):
                            names[
                                index
                            ] = nombre

                    resultado.names = names

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

                    with self.lock:
                        self._last_stream_frame_at = None


                ok, frame = cap.read()

                if not ok:
                    cap.release()

                    cap = None

                    time.sleep(
                        0.25
                    )

                    continue


                now = time.perf_counter()

                with self.lock:
                    previous = (
                        self._last_stream_frame_at
                    )

                    self._last_stream_frame_at = now

                    if (
                        previous is not None
                        and
                        now > previous
                    ):
                        instant_stream_fps = (
                            1.0
                            /
                            (now - previous)
                        )

                        self.stream_fps = (
                            self._smooth(
                                self.stream_fps,
                                instant_stream_fps
                            )
                        )


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
