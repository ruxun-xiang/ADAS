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
