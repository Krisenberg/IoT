# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=import-error

from PIL import Image, ImageDraw
import lib.oled.SSD1331 as SSD1331
DISP = SSD1331.SSD1331()

image_names_paths = {
    'rfid' : './lib/oled/rfid.png',
    'pin' : './lib/oled/writePIN.png',
    'token' : './lib/oled/writeToken.png'
}

def display_on_oled(disp, image_name):
    image = Image.open(image_names_paths[image_name])
    disp.ShowImage(image, 100, 100)

def set_oled(disp):
    disp = DISP
    disp.Init()
    disp.clear()

def clear_oled(disp):
    disp.clear()
    disp.reset()
