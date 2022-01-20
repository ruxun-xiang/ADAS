import serial
import time

s = serial.Serial('/dev/ttyUSB0', 115200)

def ser(_list, _time):
    s.write(_list)
    time.sleep(_time)


if __name__ == '__main__':
    up = [0xDE, 246, 246, 0xAA, 0xAA]
    down = [0xDE, 244, 244, 0xBB, 0xBB]
    left = [0xDE, 250, 242, 0xAA, 0xAA]
    right = [0xDE, 242, 250, 0xAA, 0xAA]
    lef = [0xCE, 0xF1, 0xAA]
    rig = [0xCE, 0xF1, 0xBB]
    #ser(up, 6)
    #ser(left, 19)
    #ser(down, 6)
    #ser(right, 19)
    #ser(lef, 8)
    #ser(rig, 8)
    ser([0xCE, 0, 0xAA], 0)
