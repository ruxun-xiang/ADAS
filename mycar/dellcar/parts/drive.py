import os
import sys
from docopt import docopt

sys.path.append("/home/mousika/mycar")
import dellcar as dk

from dellcar.parts.camera import NanoCamera, SingleCamera, DualCamera
from dellcar.parts.transform import Lambda
from dellcar.parts.keras import KerasCategorical
from dellcar.parts.tensorrt import TensorRTLinear
from dellcar.parts.actuator import PWMThrottle
from dellcar.parts.datastore import TubWriter, TubGroup
from dellcar.parts.controller import JoystickController
from dellcar import vehicle


class Drive():
    stats = None
    stop = False

    def drive(self, model_path=None):

        cfg = dk.load_config("/home/mousika/mycar/config.py")
        V = vehicle.Vehicle()
        Drive.stats = "yellow"
        cam_num = 0
        devs = os.listdir('/dev')
        for dev in devs:
            if 'video' in dev:
                cam_num += 1
        if cam_num == 1:
            cam = SingleCamera(resolution=cfg.CAMERA_RESOLUTION, iCam=0)
        elif cam_num == 2:
            cam = DualCamera(resolution=cfg.CAMERA_RESOLUTION)
        else:
            print('Cannot Support %s Cameras' % cam_num)
            raise
        V.add(cam, outputs=['cam/image_array'], threaded=True)

        if not model_path:
            ctr = JoystickController(max_throttle=cfg.JOYSTICK_MAX_THROTTLE,
                                     steering_scale=cfg.JOYSTICK_STEERING_SCALE,
                                     auto_record_on_throttle=cfg.AUTO_RECORD_ON_THROTTLE)
            V.add(ctr,
                  inputs=['cam/image_array'],
                  outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
                  threaded=True)

            def pilot_condition(mode):
                return False

            pilot_condition_part = Lambda(pilot_condition)
            V.add(pilot_condition_part, inputs=['user/mode'],
                  outputs=['run_pilot'])

            def drive_mode(mode,
                           user_angle, user_throttle):
                return user_angle, user_throttle

            drive_mode_part = Lambda(drive_mode)

            V.add(drive_mode_part,
                  inputs=['user/mode', 'user/angle', 'user/throttle'],
                  outputs=['angle', 'throttle'])

            inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode']
            types = ['image_array', 'float', 'float', 'str']

            tub = TubWriter(path=cfg.TUB_PATH, inputs=inputs, types=types)
            V.add(tub, inputs=inputs, run_condition='recording')

        else:
            def pilot_condition(mode):
                return True

            pilot_condition_part = Lambda(pilot_condition)
            V.add(pilot_condition_part, inputs=['user/mode'],
                  outputs=['run_pilot'])

            if model_path.endswith(".uff"):
                kl = TensorRTLinear()
            else:
                kl = KerasCategorical()
            kl.load(model_path)

            V.add(kl, inputs=['cam/image_array'],
                  outputs=['pilot/angle', 'pilot/throttle'],
                  run_condition='run_pilot')

            def drive_mode(mode,
                           pilot_angle, pilot_throttle):
                return pilot_angle, pilot_throttle

            drive_mode_part = Lambda(drive_mode)
            V.add(drive_mode_part,
                  inputs=['user/mode', 'pilot/angle', 'pilot/throttle'],
                  outputs=['angle', 'throttle'])

        def is_stop():
            iStop = Drive.stop
            if iStop:
                Drive.stats = None
                if model_path:
                    kl.pop()
            return iStop

        is_stop_part = Lambda(is_stop)
        V.add(is_stop_part, outputs=['is_stop'])

        throttle = PWMThrottle()
        V.add(throttle, inputs=['throttle', 'angle', 'is_stop'])

        Drive.stats = "green"
        V.start(rate_hz=cfg.DRIVE_LOOP_HZ,
                max_loop_count=cfg.MAX_LOOPS)


if __name__ == '__main__':
    d = Drive()
    d.drive("../../models/add_model")
