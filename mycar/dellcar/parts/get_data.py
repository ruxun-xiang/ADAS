class GetData():
    def __init__(self):
        import serial
        self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
        self.data = None


    def update(self):
        import time
        while self.ser.isOpen():
            self.ser.write([0xDE])
            self.data = str(self.ser.readline())
            time.sleep(0.2)

        self.ser.close()


    def run_threaded(self):
        return self.data

    def shutdown(self):
        self.data = None
