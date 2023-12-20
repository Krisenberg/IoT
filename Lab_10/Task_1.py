#!/usr/bin/env python3

from asyncio import selector_events
import time
from PIL import Image, ImageDraw, ImageFont
import lib.oled.SSD1331 as SSD1331
import os
from config import *
import w1thermsensor
import board
import busio
import threading
from threading import Thread
import adafruit_bme280.advanced as adafruit_bme280

sensorSelection = 0
lastSelectionChange = 0
backToTempPeriod = 5000
stopByGreenButton = False
stopByRedButton = False
exit = False
greenButtonPressedTimestamp = 0
redButtonPressedTimestamp = 0
BUTTON_PRESSED_COOLDOWN = 50

def readSensor_twc(sensorSelection):
    i2c = busio.I2C(board.SCL, board.SDA)
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, 0x76)
    bme280.sea_level_pressure = 1013.25
    bme280.standby_period = adafruit_bme280.STANDBY_TC_500
    bme280.iir_filter = adafruit_bme280.IIR_FILTER_X16
    bme280.overscan_pressure = adafruit_bme280.OVERSCAN_X16
    bme280.overscan_humidity = adafruit_bme280.OVERSCAN_X1
    bme280.overscan_temperature = adafruit_bme280.OVERSCAN_X2

    if (sensorSelection == 0):
        return (f'{bme280.temperature:0.1f}'+chr(176) + 'C')
    elif (sensorSelection == 1):
        return (f'{bme280.humidity:0.1f}'+'%')
    else:
        return (f'{bme280.pressure:0.1f}'+'hPa')

def runInThread(func):
    def wrapped(channel):
        t = Thread(target=func(channel))
        t.start()
    return wrapped

def redButtonPressedCallback(channel):
    global sensorSelection, lastSelectionChange, stopByRedButton, redButtonPressedTimestamp
    if (sensorSelection >= 1):
        sensorSelection -= 1
    else:
        sensorSelection = 2
    lastSelectionChange = time.time() * 1000
    stopByRedButton = True
    redButtonPressedTimestamp = int(time.time() * 1000)

def greenButtonPressedCallback(channel):
    global sensorSelection, lastSelectionChange, stopByGreenButton, greenButtonPressedTimestamp
    sensorSelection = (sensorSelection + 1) % 3
    lastSelectionChange = time.time() * 1000
    stopByGreenButton = True
    greenButtonPressedTimestamp = int(time.time() * 1000)

def getImagePath():
    global sensorSelection

    if (sensorSelection == 0):
        return './lib/oled/m_sun.jpg'
    elif (sensorSelection == 1):
        return './lib/oled/m_rain.jpg'
    else:
        return './lib/oled/m_mountains.jpg'

def oledtest(disp):

    global sensorSelection, stopByRedButton, stopByGreenButton, exit
    fontLarge = ImageFont.truetype('./lib/oled/Font.ttf', 18)

    while (not stopByRedButton or not stopByGreenButton):
        if (int(time.time() * 1000) - BUTTON_PRESSED_COOLDOWN >= redButtonPressedTimestamp):
            stopByRedButton = False
        if (int(time.time() * 1000) - BUTTON_PRESSED_COOLDOWN >= greenButtonPressedTimestamp):
            stopByGreenButton = False
        exit = True if (stopByGreenButton and stopByRedButton) else False

        if (exit):
            return
        
        if (round(time.time() * 1000) - lastSelectionChange > backToTempPeriod):
            sensorSelection = 0

        image = Image.open(getImagePath())
        draw = ImageDraw.Draw(image)
        draw.text((12, 40), readSensor_twc(sensorSelection), font=fontLarge, fill="BLACK")
        disp.ShowImage(image, 100, 100)

def test():
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=runInThread(redButtonPressedCallback), bouncetime=200)
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=runInThread(greenButtonPressedCallback), bouncetime=200)
    disp = SSD1331.SSD1331()
    disp.Init()
    disp.clear()

    global sensorSelection, lastSelectionChange, exit
    sensorSelection = 0
    lastSelectionChange = time.time() * 1000
    flag = True
    while (flag):
        oledtest(disp)
        flag = exit
    disp.clear()
    disp.reset()

if __name__ == "__main__":
    test()
    GPIO.cleanup()
