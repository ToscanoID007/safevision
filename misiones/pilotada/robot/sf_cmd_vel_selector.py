#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

import rospy

from actionlib_msgs.msg import GoalID
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from std_srvs.srv import SetBool
from std_srvs.srv import SetBoolResponse


class CmdVelSelector:
    def __init__(self):
        self.mode = "manual"

        self.timeout = float(
            rospy.get_param(
                "~timeout",
                0.5
            )
        )

        self.last_active_command = None
        self.zero_sent = False

        self.cmd_pub = rospy.Publisher(
            "/cmd_vel",
            Twist,
            queue_size=10
        )

        self.mode_pub = rospy.Publisher(
            "/safevision/control_mode",
            String,
            queue_size=1,
            latch=True
        )

        self.cancel_pub = rospy.Publisher(
            "/move_base/cancel",
            GoalID,
            queue_size=1
        )

        rospy.Subscriber(
            "/cmd_vel_manual",
            Twist,
            self.manual_callback,
            queue_size=10
        )

        rospy.Subscriber(
            "/cmd_vel_nav",
            Twist,
            self.nav_callback,
            queue_size=10
        )

        rospy.Service(
            "/safevision/set_navigation_mode",
            SetBool,
            self.set_navigation_mode
        )

        rospy.Timer(
            rospy.Duration(0.05),
            self.watchdog
        )

        self.publicar_modo()

        rospy.loginfo(
            "SafeVision cmd_vel selector: MANUAL"
        )

    def publicar_cero(self):
        self.cmd_pub.publish(
            Twist()
        )

    def detener(self):
        for _ in range(3):
            self.publicar_cero()
            rospy.sleep(0.03)

        self.last_active_command = None
        self.zero_sent = True

    def publicar_modo(self):
        self.mode_pub.publish(
            String(
                data=self.mode
            )
        )

    def manual_callback(self, msg):
        if self.mode != "manual":
            return

        self.last_active_command = time.monotonic()
        self.zero_sent = False

        self.cmd_pub.publish(
            msg
        )

    def nav_callback(self, msg):
        if self.mode != "navigation":
            return

        self.last_active_command = time.monotonic()
        self.zero_sent = False

        self.cmd_pub.publish(
            msg
        )

    def watchdog(self, _event):
        if self.last_active_command is None:
            return

        elapsed = (
            time.monotonic()
            - self.last_active_command
        )

        if (
            elapsed > self.timeout
            and not self.zero_sent
        ):
            self.publicar_cero()
            self.zero_sent = True

    def set_navigation_mode(self, request):
        self.detener()

        if request.data:
            self.mode = "navigation"

            mensaje = (
                "Modo NAVEGACION activo"
            )

        else:
            self.cancel_pub.publish(
                GoalID()
            )

            self.mode = "manual"

            mensaje = (
                "Modo MANUAL activo"
            )

        self.publicar_modo()

        rospy.loginfo(
            mensaje
        )

        return SetBoolResponse(
            success=True,
            message=mensaje
        )


def main():
    rospy.init_node(
        "sf_cmd_vel_selector"
    )

    CmdVelSelector()

    rospy.spin()


if __name__ == "__main__":
    main()
