import cv2
import time


class TestCamera():
    def __init__(self, resolution=(320, 240)):
        self.resolution = resolution
        self.framerate = 20

        self.cap1 = cv2.VideoCapture(0)
        self.cap1.set(3, resolution[0])
        self.cap1.set(4, resolution[1])
        # self.cap1.set(cv2.CAP_PROP_FPS, self.framerate)
        self.frame = None
        time.sleep(0.5)

    def run(self):
        try:
            for i in range(10):
                _, frame = self.cap1.read()
                print(frame)
        except Exception as e:
            print(e)

    def __del__(self):
        self.cap1.release()


if __name__ == '__main__':
    testC = TestCamera()
    testC.run()
