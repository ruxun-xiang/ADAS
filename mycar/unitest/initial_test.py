#Engine
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





# Camera
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


# TensorFlow
import numpy as np
import os
import cv2
from tensorflow.python.keras.models import load_model


class TensorFlowTest:

    def __init__(self):
        self.model = load_model("static/test_model")

    def run(self):
        try:
            for img in os.listdir("static"):
                if img.endswith(".jpg"):
                    img = cv2.imread(os.path.join("static", img))
                    img = np.asanyarray(img)
                    img_arr = img.reshape((1,) + img.shape)
                    angle_binned, throttle = self.model.predict(img_arr)
                    angle_unbinned = self.linear_unbin(angle_binned[0])
                    print(angle_unbinned, throttle[0][0])
        except Exception as e:
            print(e)

    def linear_unbin(self, arr):
        if not len(arr) == 15:
            raise ValueError('Illegal array length, must be 15')
        b = np.argmax(arr)
        a = b * (2 / 14) - 1
        return a


if __name__ == '__main__':
    TFTest = TensorFlowTest()
    TFTest.run()




# Tensorrt
from collections import namedtuple
#from ..dellcar.parts.keras import KerasPilot
import json
import numpy as np
import pycuda.driver as cuda
import pycuda.autoinit
from pathlib import Path
import tensorflow as tf
import tensorrt as trt
import time
import os
import cv2

HostDeviceMemory = namedtuple('HostDeviceMemory', 'host_memory device_memory')

class TensorRTLinear():
    '''
    Uses TensorRT to do the inference.
    '''
    def __init__(self, *args, **kwargs):
        super(TensorRTLinear, self).__init__(*args, **kwargs)
        self.logger = trt.Logger(trt.Logger.WARNING)
        # self.cfg = cfg
        self.engine = None
        self.inputs = None
        self.outputs = None
        self.bindings = None
        self.stream = None
        self.cfx = cuda.Device(0).make_context()

    def pop(self):
        self.cfx.pop()

    def compile(self):
        print('Nothing to compile')

    def load(self, model_path):
        uff_model = Path(model_path)
        metadata_path = Path('%s/%s.metadata' % (uff_model.parent.as_posix(), uff_model.stem))
        with open(metadata_path.as_posix(), 'r') as metadata, trt.Builder(self.logger) as builder, builder.create_network() as network, trt.UffParser() as parser:

            # Without this max_workspace_size setting, I was getting:
            # Building CUDA Engine
            # [TensorRT] ERROR: Internal error: could not find any implementation for node 2-layer MLP, try increasing the workspace size with IBuilder::setMaxWorkspaceSize()
 # [TensorRT] ERROR: ../builder/tacticOptimizer.cpp (1230) - OutOfMemory Error in computeCosts: 0
            builder.max_workspace_size = 1 << 20 #common.GiB(1)
            builder.max_batch_size = 1

            metadata = json.loads(metadata.read())
            # Configure inputs and outputs
            print('Configuring I/O')
            input_names = metadata['input_names']
            output_names = metadata['output_names']
            for name in input_names:
                parser.register_input(name, (3, 240, 320))

            for name in output_names:
                parser.register_output(name)
            # Parse network
            print('Parsing TensorRT Network')
            parser.parse(uff_model.as_posix(), network)
            print('Building CUDA Engine')
            self.engine = builder.build_cuda_engine(network)
            # Allocate buffers
            print('Allocating Buffers')
            self.inputs, self.outputs, self.bindings, self.stream = TensorRTLinear.allocate_buffers(self.engine)
            print('Ready')

    def run(self, image):
        start_time = time.time()
        # Channel first image format
        image = image.transpose((2,0,1))
        # Flatten it to a 1D array.
        image = image.ravel()
        # The first input is the image. Copy to host memory.
        image_input = self.inputs[0]
        np.copyto(image_input.host_memory, image)
        with self.engine.create_execution_context() as context:
            [throttle, steering] = TensorRTLinear.infer(context=context, bindings=self.bindings, inputs=self.inputs, outputs=self.outputs, stream=self.stream)
            steering  = self.linear_unbin(steering)
            print("used_time: ", time.time() - start_time, "steering: ", steering, "throttle: ", throttle[0])
            return steering, throttle[0]

    def linear_unbin(self, arr):
        """
        Convert a categorical array to value.

        See Also
        --------
        linear_bin
        """
        if not len(arr) == 15:
            raise ValueError('Illegal array length, must be 15')
        b = np.argmax(arr)
        a = b * (2 / 14) - 1
        return a


    @classmethod
    def allocate_buffers(cls, engine):
        inputs = []
        outputs = []
        bindings = []
        stream = cuda.Stream()
        for binding in engine:
            size = trt.volume(engine.get_binding_shape(binding)) * engine.max_batch_size
            dtype = trt.nptype(engine.get_binding_dtype(binding))
            # Allocate host and device buffers
            host_memory = cuda.pagelocked_empty(size, dtype)
            device_memory = cuda.mem_alloc(host_memory.nbytes)
            bindings.append(int(device_memory))
            if engine.binding_is_input(binding):
                inputs.append(HostDeviceMemory(host_memory, device_memory))
            else:
                outputs.append(HostDeviceMemory(host_memory, device_memory))

        return inputs, outputs, bindings, stream

    @classmethod
    def infer(cls, context, bindings, inputs, outputs, stream, batch_size=1):
        # Transfer input data to the GPU.
        [cuda.memcpy_htod_async(inp.device_memory, inp.host_memory, stream) for inp in inputs]
        # Run inference.
        context.execute_async(batch_size=batch_size, bindings=bindings, stream_handle=stream.handle)
        # Transfer predictions back from the GPU.
        [cuda.memcpy_dtoh_async(out.host_memory, out.device_memory, stream) for out in outputs]
        # Synchronize the stream
        stream.synchronize()
        # Return only the host outputs.
        return [out.host_memory for out in outputs]

if __name__ == '__main__':
    kl = TensorRTLinear()
    kl.load("/home/mousika/mycar/models/add_model.uff")

    for img in os.listdir("/home/mousika/mycar/unitest/static"):
        if img.endswith("jpg"):
            img = cv2.imread("/home/mousika/mycar/unitest/static/%s"%img)
            kl.run(img)
    kl.pop()

