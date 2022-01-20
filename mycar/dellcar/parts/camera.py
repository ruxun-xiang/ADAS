import os
import time
import numpy as np
from PIL import Image
import glob
from threading import Thread
import cv2
from datetime import datetime


class BaseCamera:

    def run_threaded(self):
        return self.frame


class NanoCamera(BaseCamera):
    def __init__(self, resolution=(320, 240), framerate=10, iCam=0):
        import pygame
        import pygame.camera
        import serial

        super().__init__()

        pygame.init()
        pygame.camera.init()
        l = pygame.camera.list_cameras()
        self.cam1 = pygame.camera.Camera(l[iCam], resolution, "RGB")
        # self.cam2 = pygame.camera.Camera(l[iCamR], resolution, "RGB")
        self.resolution = resolution
        self.cam1.start()
        # self.cam2.start()
        self.framerate = 10

        # initialize variable used to indicate
        # if the thread should be stopped
        #self.frame1 = None
        #self.frame2 = None
        self.frame = None
        self.on = True
        self.display = display
        self.server_ip = '192.168.1.166'
        self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)

        print('NanoCam loaded.. .warming camera')

        time.sleep(2)

    def update(self):
        from datetime import datetime, timedelta
        import pygame.image
        while self.on:
            start = datetime.now()

            if self.cam1.query_image():
                # snapshot = self.cam.get_image()
                # self.frame = list(pygame.image.tostring(snapshot, "RGB", False))
                snapshotL = self.cam1.get_image()
                snapshot1L = pygame.transform.scale(snapshotL, self.resolution)
                self.frame = pygame.surfarray.pixels3d(
                    pygame.transform.rotate(pygame.transform.flip(snapshot1L, True, False), 90))

                #snapshotR = self.cam2.get_image()
                #snapshot1R = pygame.transform.scale(snapshotR, self.resolution)
                #self.frame2 = pygame.surfarray.pixels3d(
                #    pygame.transform.rotate(pygame.transform.flip(snapshot1R, True, False), 90))

                # self.frame = cv2.resize(frame, dsize=(160,120), interpolation=cv2.INTER_CUBIC)
                self.frame = np.asanyarray(self.frame)
                #self.frame2 = np.asanyarray(self.frame2)

                # self.frame1 = cv2.resize(self.frame1, dsize=(320,240), interpolation=cv2.INTER_CUBIC)
                # self.frame2 = cv2.resize(self.frame2, dsize=(320,240), interpolation=cv2.INTER_CUBIC)

                #self.frame = np.hstack((self.frame1, self.frame2))

                if self.display:
                    # colori_img = np.asanyarray(self.frame1)
                    data = {}
                    self.ser.write([0xDE])
                    carData = str(self.ser.readline())
                    # print('carData no.2: {}'.format(carData))
                    data['data'] = carData
                    try:
                        # print('inside')
                        t1 = Thread(target=sendJson, args=(self.server_ip, data))
                        t1.start()
                        img = np.asanyarray(self.frame)
                        t2 = Thread(target=sendFile, args=(self.server_ip, img))
                        t2.start()
                    except:
                        print('Connection fail')
            # print('end loop')
            stop = datetime.now()
            s = 1 / self.framerate - (stop - start).total_seconds()
            if s > 0:
                time.sleep(s)

        self.cam1.stop()
        #self.cam2.stop()

    def run_threaded(self):
        return self.frame

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping NanoCam')
        time.sleep(.5)

class SingleCamera(BaseCamera):
    def __init__(self, resolution=(640, 480), framerate=10, iCam=0):
        self.resolution = resolution
        self.framerate = 20

        self.cap1 = cv2.VideoCapture(0)
        self.cap1.set(3, resolution[0])
        self.cap1.set(4, resolution[1])
        # self.cap1.set(cv2.CAP_PROP_FPS, self.framerate)
        self.frame = None
        self.on = True
        time.sleep(0.5)

    def update(self):
        while self.on:
            start = datetime.now()
            ret, frame = self.cap1.read()
            self.frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            stop = datetime.now()
            s = 1 / self.framerate - (stop - start).total_seconds()
            if s > 0:
                time.sleep(s)

    def run_threaded(self):
        return self.frame

    def shutdown(self):
        self.on = False
        cap1.release()
        print('stoping NanoCam')
        time.sleep(.5)


class DualCamera(BaseCamera):
    def __init__(self, resolution=(320, 240)):
        self.resolution = resolution
        self.framerate = 20

        self.cap1 = cv2.VideoCapture(0)
        self.cap1.set(3, resolution[0])
        self.cap1.set(4, resolution[1])
        # self.cap1.set(cv2.CAP_PROP_FPS, self.framerate)

        self.cap2 = cv2.VideoCapture(1)
        self.cap2.set(3, resolution[0])
        self.cap2.set(4, resolution[1])
        # self.cap2.set(cv2.CAP_PROP_FPS, self.framerate)

        # initialize variable used to indicate
        # if the thread should be stopped
        self.frame1 = None
        self.frame2 = None
        self.frame = None
        self.on = True

        print('DualCam loaded.. .warming camera')

        time.sleep(0.5)

    def update(self):
        from datetime import datetime, timedelta
        while self.on:
            start = datetime.now()

            ret1, frame1 = self.cap1.read()
            ret2, frame2 = self.cap2.read()

            self.frame1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2BGR)
            self.frame2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2BGR)

            self.frame1 = self.frame1[0:240, 0:220]
            self.frame2 = self.frame2[0:240, 100:320]
            self.frame1 = np.asanyarray(self.frame1)
            self.frame2 = np.asanyarray(self.frame2)

            # self.frame1 = cv2.resize(self.frame1, dsize=(320,240), interpolation=cv2.INTER_CUBIC)
            # self.frame2 = cv2.resize(self.frame2, dsize=(320,240), interpolation=cv2.INTER_CUBIC)

            self.frame = np.hstack((self.frame1, self.frame2))


            stop = datetime.now()
            s = 1 / self.framerate - (stop - start).total_seconds()
            if s > 0:
                time.sleep(s)

    def run_threaded(self):
        return self.frame

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        cap1.release()
        cap2.release()
        print('stoping NanoCam')
        time.sleep(.5)


class MockCamera(BaseCamera):
    """
    Fake camera. Returns only a single static frame
    """

    def __init__(self, resolution=(160, 120), image=None):
        if image is not None:
            self.frame = image
        else:
            self.frame = Image.new('RGB', resolution)

    def update(self):
        pass

    def shutdown(self):
        pass


class ImageListCamera(BaseCamera):
    """
    Use the images from a tub as a fake camera output
    """

    def __init__(self, path_mask='~/mycar/data/**/*.jpg'):
        self.image_filenames = glob.glob(os.path.expanduser(path_mask), recursive=True)

        def get_image_index(fnm):
            sl = os.path.basename(fnm).split('_')
            return int(sl[0])

        """
        I feel like sorting by modified time is almost always
        what you want. but if you tared and moved your data around,
        sometimes it doesn't preserve a nice modified time.
        so, sorting by image index works better, but only with one path.
        """
        self.image_filenames.sort(key=get_image_index)
        # self.image_filenames.sort(key=os.path.getmtime)
        self.num_images = len(self.image_filenames)
        print('%d images loaded.' % self.num_images)
        print(self.image_filenames[:10])
        self.i_frame = 0
        self.frame = None
        self.update()

    def update(self):
        pass

    def run_threaded(self):
        if self.num_images > 0:
            self.i_frame = (self.i_frame + 1) % self.num_images
            self.frame = Image.open(self.image_filenames[self.i_frame])

        return np.asarray(self.frame)

    def shutdown(self):
        pass
