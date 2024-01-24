# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=import-error

from PIL import Image, ImageDraw, ImageFont

def display_on_oled(disp, oled_cursor_position, encoder_number):
    image = Image.new("RGB", (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image)
    font_large = ImageFont.truetype('./lib/oled/Font.ttf', 20)

    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    if oled_cursor_position == 0:
        draw.text((8, 0), f'{encoder_number:02d}', font=font_large, fill="WHITE")
    else:
        draw.text((8, 30), f'{encoder_number:02d}', font=font_large, fill="WHITE")

def set_oled(disp):
    disp.Init()
    disp.clear()
    image = Image.new("RGB", (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image)
    font_large = ImageFont.truetype('./lib/oled/Font.ttf', 20)

    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    draw.text((8, 0), '0', font=font_large, fill="WHITE")
    draw.text((8, 30),'0', font=font_large, fill="WHITE")

def clear_oled(disp):
    disp.clear()
    disp.reset()
