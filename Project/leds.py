#!/usr/bin/env python3

from config import *  # pylint: disable=unused-wildcard-import
import board
import neopixel
import time
import threading
import logging
from terminal_colors import TerminalColors

def pixelsAccept():
    pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
    pixels.fill((0, 255, 0))
    pixels.show()
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  PIXELS ARE GREEN{TerminalColors.RESET}')

def pixelsDeny():
    pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
    pixels.fill((255, 0, 0))
    pixels.show()
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  PIXELS ARE RED{TerminalColors.RESET}')

def cleanPixels():
    pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
    pixels.fill((0, 0, 0))
    pixels.show()
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  pixels are clear{TerminalColors.RESET}')

def ledsAccept(duration):
    pixelsAccept()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()

def ledsDeny(duration):
    pixelsDeny()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()