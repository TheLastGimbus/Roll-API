import gpiozero
import os
import pathlib
import subprocess
import uuid
from flask import Flask
from flask import send_file
from time import sleep
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
if bool(os.getenv['FLASK_REVERSE_PROXY']):
    # Use this if you're using a reverse-proxy to get real IPs
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

API1 = '/api/v1'

FULL_IMAGES = pathlib.Path('full_images/')

led = gpiozero.LED(4)


def roll_dice():
    s = gpiozero.Servo(14, min_pulse_width=1 / 2000)  # Default pulse isn't getting full 180 degrees
    s.min()
    sleep(0.5)
    s.value = 0.9
    sleep(0.5)
    s.close()  # Close it so it doesn't rattle in there


# https://raspberrypi.stackexchange.com/questions/51406/cannot-connect-to-picamera-when-using-it-with-flask
# Change this later possibly
def take_picture(out_name):
    led.on()
    subprocess.run(f'raspistill -o {out_name}'.split(' '))
    led.off()


@app.route(API1)
def hello():
    return "Hello there!"


@app.route(API1 + '/roll')
def roll():
    roll_dice()
    image_id = str(uuid.uuid4())
    pic_name = FULL_IMAGES / f'{image_id}.jpg'
    take_picture(pic_name)
    # TODO: Recognize dice
    return {'full_image_id': image_id}


@app.route(API1 + '/image/<uuid:image_id>')
def image(image_id):
    return send_file(FULL_IMAGES / f'{image_id}.jpg')
