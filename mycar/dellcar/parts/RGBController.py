#!/usr/bin/python
# -*- coding: UTF-8 -*-

import RPi.GPIO as GPIO
#from redisStore import redisDB
import time

class RGBLedSetter:
    def __init__(self):
        self.R_LED = 11  # GPIO17
        self.G_LED = 12  # GPIO18
        self.B_LED = 13  # GPIO27
  #      self.myRedis = redisDB()
 #       self.myRedis.update_led_status(False, False, True)

        GPIO.setwarnings(False)        # Disable warnings
        GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
        GPIO.setup(self.R_LED, GPIO.OUT)  # Set pins' mode is output
        GPIO.output(self.R_LED, GPIO.LOW)  # Set pins to high(+3.3V) to off led
        GPIO.setup(self.G_LED, GPIO.OUT)
        GPIO.output(self.G_LED, GPIO.LOW)
        GPIO.setup(self.B_LED, GPIO.OUT)
        GPIO.output(self.B_LED, GPIO.LOW)

        self.p_R = GPIO.PWM(self.R_LED, 2000)  # set Frequece to 2KHz
        self.p_G = GPIO.PWM(self.G_LED, 2000)
        self.p_B = GPIO.PWM(self.B_LED, 2000)

        self.p_R.start(0)      # Initial duty Cycle = 0(leds off)
        self.p_G.start(0)
        self.p_B.start(0)


    def R_Led_on(self):
        self.p_R.ChangeDutyCycle(100)
        self.p_G.ChangeDutyCycle(0)
        self.p_B.ChangeDutyCycle(0)
   #     self.myRedis.update_led_status(True, False, False)
#        time.sleep(0.4)

    def G_Led_on(self):
        self.p_R.ChangeDutyCycle(0)
        self.p_G.ChangeDutyCycle(100)
        self.p_B.ChangeDutyCycle(0)
    #    self.myRedis.update_led_status(False, True, False)
        time.sleep(0.4)

    def B_Led_on(self):
        self.p_R.ChangeDutyCycle(0)
        self.p_G.ChangeDutyCycle(0)
        self.p_B.ChangeDutyCycle(100)
     #   self.myRedis.update_led_status(False, False, True)
 #       time.sleep(0.4)

    def all_Led_off(self):
        self.p_R.ChangeDutyCycle(0)
        self.p_G.ChangeDutyCycle(0)
        self.p_B.ChangeDutyCycle(0)
      #  self.myRedis.update_led_status(False, False, False)
  #      time.sleep(0.4)
        GPIO.cleanup


if __name__ == "__main__":
    myLedSetter = RGBLedSetter()

    try:
        while True:
            print("all off")
            myLedSetter.all_Led_off()
            time.sleep(3)
            print ("R ON")
            myLedSetter.R_Led_on()
            time.sleep(3)
            print ("all off")
            myLedSetter.all_Led_off()
            time.sleep(3)
            print ("G ON")
            myLedSetter.G_Led_on()
            time.sleep(3)
            print ("all off")
            myLedSetter.all_Led_off()
            time.sleep(3)
            print ("B ON")
            myLedSetter.B_Led_on()
            time.sleep(3)

    except KeyboardInterrupt:
        myLedSetter.p_R.stop()
        myLedSetter.p_G.stop()
        myLedSetter.p_B.stop()
        GPIO.cleanup()
