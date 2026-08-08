#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import os
import time

import rospy
import tf

from geometry_msgs.msg import PoseWithCovarianceStamped


POSE_OUTPUT = "/tmp/safevision_map_pose.json"
POSE_TEMP = POSE_OUTPUT + ".tmp"

INITIALPOSE_REQUEST = (
    "/tmp/safevision_initialpose_request.json"
)

INITIALPOSE_ACK = (
    "/tmp/safevision_initialpose_ack.json"
)

FRAME_MAP = "map"
FRAME_ROBOT = "base_footprint"

FRECUENCIA_HZ = 10.0


def escribir_json_atomico(ruta, datos):
    temporal = ruta + ".tmp"

    with open(temporal, "w") as archivo:
        json.dump(
            datos,
            archivo,
            sort_keys=True
        )

    os.rename(
        temporal,
        ruta
    )


def guardar_pose(x, y, yaw):
    datos = {
        "ok": True,
        "frame_id": FRAME_MAP,
        "child_frame_id": FRAME_ROBOT,

        "x": float(x),
        "y": float(y),

        "yaw": float(yaw),
        "yaw_deg": float(
            math.degrees(yaw)
        ),

        "ros_stamp": float(
            rospy.Time.now().to_sec()
        ),

        "updated_at": float(
            time.time()
        ),

        "source": (
            "tf_map_base_footprint"
        )
    }

    escribir_json_atomico(
        POSE_OUTPUT,
        datos
    )


def leer_request_id_actual():
    if not os.path.exists(
        INITIALPOSE_REQUEST
    ):
        return None

    try:
        with open(
            INITIALPOSE_REQUEST,
            "r"
        ) as archivo:
            datos = json.load(
                archivo
            )

        return datos.get(
            "request_id"
        )

    except Exception:
        return None


def publicar_initialpose(
    publisher,
    datos
):
    x = float(
        datos["x"]
    )

    y = float(
        datos["y"]
    )

    yaw = float(
        datos["yaw"]
    )

    request_id = datos[
        "request_id"
    ]

    quaternion = (
        tf.transformations
        .quaternion_from_euler(
            0.0,
            0.0,
            yaw
        )
    )

    mensaje = (
        PoseWithCovarianceStamped()
    )

    mensaje.header.stamp = (
        rospy.Time.now()
    )

    mensaje.header.frame_id = (
        FRAME_MAP
    )

    mensaje.pose.pose.position.x = x
    mensaje.pose.pose.position.y = y
    mensaje.pose.pose.position.z = 0.0

    mensaje.pose.pose.orientation.x = (
        quaternion[0]
    )

    mensaje.pose.pose.orientation.y = (
        quaternion[1]
    )

    mensaje.pose.pose.orientation.z = (
        quaternion[2]
    )

    mensaje.pose.pose.orientation.w = (
        quaternion[3]
    )

    # Incertidumbre moderada similar a una
    # estimacion manual de pose.
    mensaje.pose.covariance[0] = 0.25
    mensaje.pose.covariance[7] = 0.25

    mensaje.pose.covariance[35] = (
        0.06853891945200942
    )

    # Publicar varias veces para asegurar que AMCL
    # alcance a recibir la correccion.
    for _ in range(3):
        publisher.publish(
            mensaje
        )

        rospy.sleep(
            0.10
        )

    ack = {
        "ok": True,
        "request_id": request_id,

        "x": x,
        "y": y,

        "yaw": yaw,
        "yaw_deg": math.degrees(
            yaw
        ),

        "published_at": time.time()
    }

    escribir_json_atomico(
        INITIALPOSE_ACK,
        ack
    )

    rospy.loginfo(
        (
            "SafeVision initialpose publicado: "
            "x=%.3f y=%.3f yaw=%.1f deg"
        ),
        x,
        y,
        math.degrees(yaw)
    )


def main():
    rospy.init_node(
        "safevision_pose_exporter",
        anonymous=False
    )

    listener = (
        tf.TransformListener()
    )

    initialpose_pub = (
        rospy.Publisher(
            "/initialpose",
            PoseWithCovarianceStamped,
            queue_size=1
        )
    )

    # Evita volver a aplicar una solicitud vieja
    # si el exporter se reinicia.
    ultimo_request_id = (
        leer_request_id_actual()
    )

    rospy.loginfo(
        "SafeVision pose/exporter iniciado"
    )

    rate = rospy.Rate(
        FRECUENCIA_HZ
    )

    primera_pose = True

    while not rospy.is_shutdown():

        # -----------------------------------------
        # TF map -> base_footprint
        # -----------------------------------------

        try:
            translation, rotation = (
                listener.lookupTransform(
                    FRAME_MAP,
                    FRAME_ROBOT,
                    rospy.Time(0)
                )
            )

            _, _, yaw = (
                tf.transformations
                .euler_from_quaternion(
                    rotation
                )
            )

            guardar_pose(
                translation[0],
                translation[1],
                yaw
            )

            if primera_pose:
                rospy.loginfo(
                    (
                        "TF disponible. "
                        "Exportando pose a 10 Hz"
                    )
                )

                primera_pose = False

        except (
            tf.LookupException,
            tf.ConnectivityException,
            tf.ExtrapolationException
        ) as exc:

            rospy.logwarn_throttle(
                2.0,
                (
                    "Esperando TF "
                    "map -> base_footprint: %s"
                )
                % exc
            )

        # -----------------------------------------
        # Nueva solicitud /initialpose
        # -----------------------------------------

        try:
            if os.path.exists(
                INITIALPOSE_REQUEST
            ):
                with open(
                    INITIALPOSE_REQUEST,
                    "r"
                ) as archivo:
                    solicitud = json.load(
                        archivo
                    )

                request_id = (
                    solicitud.get(
                        "request_id"
                    )
                )

                if (
                    request_id
                    and
                    request_id
                    != ultimo_request_id
                ):
                    publicar_initialpose(
                        initialpose_pub,
                        solicitud
                    )

                    ultimo_request_id = (
                        request_id
                    )

        except Exception as exc:
            rospy.logerr_throttle(
                2.0,
                (
                    "Error procesando "
                    "initialpose: %s"
                )
                % exc
            )

        rate.sleep()


if __name__ == "__main__":
    try:
        main()

    except rospy.ROSInterruptException:
        pass
