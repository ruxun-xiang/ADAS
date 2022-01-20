import serial
import time

s = serial.Serial('/dev/ttyUSB0', 115200)


def ser(_list, _time):
    s.write(_list)
    time.sleep(_time)


if __name__ == '__main__':
    up = [0xDE, 200, 200, 0xAA, 0xAA]
    down = [0xDE, 200, 200, 0xBB, 0xBB]
    left = [0xDE, 240, 200, 0xAA, 0xAA]
    right = [0xDE, 200, 240, 0xAA, 0xAA]
    lef = [0xCE, 0xF1, 0xAA]
    rig = [0xCE, 0xF1, 0xBB]
    ser(up, 2)
    ser(left, 2)
    ser(down, 2)
    ser(right, 2)
    ser(lef, 1)
    ser(rig, 1)
    ser([0xCE, 0, 0xAA], 0)
