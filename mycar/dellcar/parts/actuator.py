"""
actuators.py
Classes to control the motors and servos. These classes
are wrapped in a mixer class before being used in the drive loop.
"""
import serial
import time
import sys
import subprocess


# import Jetson.GPIO as GPIO

class PWMThrottle:
    """
    Wrapper over a PWM motor cotnroller to convert -1 to 1 throttle
    values to PWM pulses.
    """

    def __init__(self):
        self.left_status = 0xAA
        self.right_status = 0xAA
        self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
        self.speed = 246
        time.sleep(3)

    def __del__(self):
        self.ser.write([0xDE, 0, 0, 0xAA, 0xAA])

    def run(self, throttle=0, angle=0):

        if angle > 0.3:
            angle = 1
        elif angle < -0.3:
            angle = -1
        else:
            angle = 0
        if throttle is None:
            return
        if throttle > 0:
            throttle = 1
 
        forward = 1
        if throttle > 0:
            self.speed = 248
            forward = 1
            self.left_status = 0xAA
            self.right_status = 0xAA
        elif throttle < 0:
            self.speed = 240
            forward = -1
            self.left_status = 0xBB
            self.right_status = 0xBB
        else:
            self.left_status = 0xAA
            self.right_status = 0xAA

        if angle == 0 and throttle != 0:
            self.left = self.speed
            self.right = self.speed
        elif angle != 0 and throttle != 0:
            if angle > 0:
                self.left = self.speed + 9 * angle * forward // 1
                self.right = self.speed - 23 * angle * forward // 1
            else:
                self.left = self.speed + 23 * angle * forward // 1
                self.right = self.speed - 9 * angle * forward // 1
        else:
            self.left = 0
            self.right = 0

        data = [0xDE, min(self.right, 250), min(self.left, 250), self.left_status, self.right_status]
        # print(data)
        self.ser.write(data)

    def shutdown(self):
        self.ser.write([0xDE, 0, 0, 0xAA, 0xAA])  # stop vehicle

