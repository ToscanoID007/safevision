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

        # SAFEVISION 7E - SHARED INFERENCE STREAM
        # Un único productor realiza captura + inferencia + JPEG.
        # Todos los clientes /video_feed consumen el último frame.
        self._shared_stream_condition = (
            threading.Condition(
                threading.RLock()
            )
        )

        self._shared_stream_thread = None
        self._shared_stream_url = None
        self._shared_stream_stop = False

        self._shared_stream_jpeg = None
        self._shared_stream_version = 0

        self._shared_stream_clients = 0
        self._shared_stream_idle_since = None

        # SAFEVISION 7F - LATEST FRAME CAPTURE
        #
        # La captura corre SIEMPRE separada de YOLO.
        # Si la cámara produce más cuadros de los que YOLO puede
        # procesar, los cuadros viejos se descartan y solamente
        # se procesa el más nuevo. Así no se acumulan segundos
        # de video atrasado.
        self._source_capture_thread = None
        self._source_capture_url = None
        self._source_capture_stop = False

        self._source_capture_frame = None
        self._source_capture_version = 0
        self._source_capture_at = None




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


    def _shared_stream_start(
        self,
        stream_url
    ):
        previous = None

        with self._shared_stream_condition:
            current = self._shared_stream_thread

            if (
                current is not None
                and current.is_alive()
                and self._shared_stream_url
                == stream_url
            ):
                return

            if (
                current is not None
                and current.is_alive()
            ):
                self._shared_stream_stop = True

                self._shared_stream_condition.notify_all()

                previous = current


        if previous is not None:
            previous.join(
                timeout=2.0
            )


        with self._shared_stream_condition:
            current = self._shared_stream_thread

            if (
                current is not None
                and current.is_alive()
                and self._shared_stream_url
                == stream_url
            ):
                return

            if (
                current is not None
                and current.is_alive()
            ):
                raise RuntimeError(
                    "El stream IA anterior no terminó."
                )

            self._shared_stream_url = (
                stream_url
            )

            self._shared_stream_stop = False

            self._shared_stream_jpeg = None
            self._shared_stream_version = 0

            worker = threading.Thread(
                target=self._shared_stream_worker,
                args=(stream_url,),
                name="safevision-inference-stream",
                daemon=True
            )

            self._shared_stream_thread = worker

            worker.start()


    def _source_capture_start(
        self,
        stream_url
    ):
        previous = None

        with self._shared_stream_condition:
            current = (
                self._source_capture_thread
            )

            if (
                current is not None
                and current.is_alive()
                and self._source_capture_url
                == stream_url
                and not self._source_capture_stop
            ):
                return

            if (
                current is not None
                and current.is_alive()
            ):
                self._source_capture_stop = True

                self._shared_stream_condition.notify_all()

                previous = current


        if previous is not None:
            previous.join(
                timeout=2.5
            )


        with self._shared_stream_condition:
            current = (
                self._source_capture_thread
            )

            if (
                current is not None
                and current.is_alive()
            ):
                raise RuntimeError(
                    "La captura anterior no terminó."
                )

            self._source_capture_url = (
                stream_url
            )

            self._source_capture_stop = False

            self._source_capture_frame = None
            self._source_capture_version = 0
            self._source_capture_at = None

            worker = threading.Thread(
                target=self._source_capture_worker,
                args=(stream_url,),
                name="safevision-latest-frame-capture",
                daemon=True
            )

            self._source_capture_thread = (
                worker
            )

            worker.start()


    def _source_capture_worker(
        self,
        stream_url
    ):
        cap = None

        try:
            while True:
                with self._shared_stream_condition:
                    if (
                        self._source_capture_stop
                        or
                        self._shared_stream_stop
                        or
                        self._source_capture_url
                        != stream_url
                    ):
                        break


                if (
                    cap is None
                    or
                    not cap.isOpened()
                ):
                    if cap is not None:
                        cap.release()

                    print(
                        "[VIDEO] Captura latest-frame conectando a {}".format(
                            stream_url
                        )
                    )

                    cap = cv2.VideoCapture(
                        stream_url
                    )

                    try:
                        cap.set(
                            cv2.CAP_PROP_BUFFERSIZE,
                            1
                        )
                    except Exception:
                        pass

                    if not cap.isOpened():
                        time.sleep(
                            0.25
                        )

                        continue


                ok, frame = cap.read()

                if not ok:
                    cap.release()
                    cap = None

                    time.sleep(
                        0.10
                    )

                    continue


                captured_at = (
                    time.monotonic()
                )


                with self._shared_stream_condition:
                    if (
                        self._source_capture_stop
                        or
                        self._shared_stream_stop
                        or
                        self._source_capture_url
                        != stream_url
                    ):
                        break

                    # Reemplazar, jamás encolar.
                    self._source_capture_frame = (
                        frame
                    )

                    self._source_capture_version += 1

                    self._source_capture_at = (
                        captured_at
                    )

                    self._shared_stream_condition.notify_all()


        except Exception as exc:
            print(
                "[VIDEO] Captura latest-frame error: {}".format(
                    exc
                )
            )


        finally:
            if cap is not None:
                cap.release()

            with self._shared_stream_condition:
                if (
                    self._source_capture_thread
                    is threading.current_thread()
                ):
                    self._source_capture_thread = None

                self._source_capture_stop = False

                self._shared_stream_condition.notify_all()


    def _shared_stream_worker(
        self,
        stream_url
    ):
        source_thread = None
        last_source_version = -1

        try:
            self._source_capture_start(
                stream_url
            )


            while True:
                frame = None
                captured_at = None
                source_version = (
                    last_source_version
                )


                with self._shared_stream_condition:
                    if self._shared_stream_stop:
                        break

                    clients = int(
                        self._shared_stream_clients
                        or
                        0
                    )

                    idle_since = (
                        self._shared_stream_idle_since
                    )


                    if (
                        clients <= 0
                        and
                        idle_since is not None
                        and
                        (
                            time.monotonic()
                            -
                            idle_since
                        )
                        >= 2.0
                    ):
                        break


                    while True:
                        if self._shared_stream_stop:
                            break

                        clients = int(
                            self._shared_stream_clients
                            or
                            0
                        )

                        idle_since = (
                            self._shared_stream_idle_since
                        )

                        if (
                            clients <= 0
                            and
                            idle_since is not None
                            and
                            (
                                time.monotonic()
                                -
                                idle_since
                            )
                            >= 2.0
                        ):
                            break


                        version = int(
                            self._source_capture_version
                            or
                            0
                        )

                        source_frame = (
                            self._source_capture_frame
                        )

                        if (
                            source_frame is not None
                            and
                            version
                            != last_source_version
                        ):
                            # El capturador crea un ndarray nuevo
                            # por cada read(); tomar la referencia
                            # es suficiente y evita otra copia.
                            frame = source_frame

                            source_version = version

                            captured_at = (
                                self._source_capture_at
                            )

                            break


                        source_thread = (
                            self._source_capture_thread
                        )

                        if (
                            source_thread is None
                            or
                            not source_thread.is_alive()
                        ):
                            break


                        self._shared_stream_condition.wait(
                            timeout=0.25
                        )


                if self._shared_stream_stop:
                    break


                if frame is None:
                    clients = int(
                        self._shared_stream_clients
                        or
                        0
                    )

                    idle_since = (
                        self._shared_stream_idle_since
                    )

                    if (
                        clients <= 0
                        and
                        idle_since is not None
                        and
                        (
                            time.monotonic()
                            -
                            idle_since
                        )
                        >= 2.0
                    ):
                        break


                    self._source_capture_start(
                        stream_url
                    )

                    time.sleep(
                        0.02
                    )

                    continue


                # Marcar YA este source frame como consumido.
                # Si durante YOLO llegan 5, 10 o 20 nuevos,
                # en la siguiente vuelta saltaremos directo
                # al más reciente.
                last_source_version = (
                    source_version
                )


                output_started = (
                    time.perf_counter()
                )


                processed = self.procesar_frame(
                    frame
                )


                correcto, buffer = cv2.imencode(
                    ".jpg",
                    processed,
                    [
                        int(
                            cv2.IMWRITE_JPEG_QUALITY
                        ),
                        80
                    ]
                )

                if not correcto:
                    continue


                payload = buffer.tobytes()


                output_at = (
                    time.perf_counter()
                )


                with self.lock:
                    previous = (
                        self._last_stream_frame_at
                    )

                    self._last_stream_frame_at = (
                        output_at
                    )

                    if (
                        previous is not None
                        and
                        output_at > previous
                    ):
                        instant_stream_fps = (
                            1.0
                            /
                            (
                                output_at
                                -
                                previous
                            )
                        )

                        self.stream_fps = (
                            self._smooth(
                                self.stream_fps,
                                instant_stream_fps
                            )
                        )


                if captured_at is not None:
                    age_ms = (
                        time.monotonic()
                        -
                        captured_at
                    ) * 1000.0

                    # Diagnóstico ocasional si por alguna razón
                    # el frame procesado vuelve a envejecer.
                    if age_ms > 750.0:
                        print(
                            "[VIDEO] Aviso: frame procesado con {:.0f} ms de edad.".format(
                                age_ms
                            )
                        )


                with self._shared_stream_condition:
                    if (
                        self._shared_stream_url
                        != stream_url
                    ):
                        break

                    self._shared_stream_jpeg = (
                        payload
                    )

                    self._shared_stream_version += 1

                    self._shared_stream_condition.notify_all()


        except Exception as exc:
            print(
                "[VIDEO] Productor IA latest-frame error: {}".format(
                    exc
                )
            )


        finally:
            with self._shared_stream_condition:
                self._source_capture_stop = True

                source_thread = (
                    self._source_capture_thread
                )

                if (
                    self._shared_stream_thread
                    is threading.current_thread()
                ):
                    self._shared_stream_thread = None

                    self._shared_stream_stop = False

                self._shared_stream_condition.notify_all()


            if (
                source_thread is not None
                and
                source_thread.is_alive()
            ):
                source_thread.join(
                    timeout=2.5
                )


    def generar_stream(
        self,
        stream_url
    ):
        with self._shared_stream_condition:
            self._shared_stream_clients += 1

            self._shared_stream_idle_since = None


        self._shared_stream_start(
            stream_url
        )


        last_version = -1


        try:
            while True:
                payload = None
                version = last_version

                with self._shared_stream_condition:
                    while True:
                        if (
                            self._shared_stream_url
                            != stream_url
                        ):
                            return

                        version = int(
                            self._shared_stream_version
                            or
                            0
                        )

                        if (
                            self._shared_stream_jpeg
                            is not None
                            and
                            version
                            != last_version
                        ):
                            payload = (
                                self._shared_stream_jpeg
                            )

                            break


                        worker = (
                            self._shared_stream_thread
                        )

                        if (
                            worker is None
                            or
                            not worker.is_alive()
                        ):
                            break


                        self._shared_stream_condition.wait(
                            timeout=1.0
                        )


                if payload is None:
                    self._shared_stream_start(
                        stream_url
                    )

                    continue


                last_version = version


                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    +
                    payload
                    +
                    b"\r\n"
                )


        except GeneratorExit:
            return


        finally:
            with self._shared_stream_condition:
                self._shared_stream_clients = max(
                    0,
                    int(
                        self._shared_stream_clients
                        or
                        0
                    )
                    -
                    1
                )

                if (
                    self._shared_stream_clients
                    <=
                    0
                ):
                    self._shared_stream_idle_since = (
                        time.monotonic()
                    )

                self._shared_stream_condition.notify_all()
