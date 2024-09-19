"""
Roll the dice and take image
This is for possible future change - using picamera library is kinda problematic (keeping camera open while running
Flask crashes :/ ) - perhaps I will use some plain USB camera in the future
"""
import gpiozero
import io
import subprocess
from picamera2 import Picamera2
from time import sleep

led = gpiozero.LED(4)


def roll_and_take_image():
    s = gpiozero.Servo(14, min_pulse_width=1 / 2000)  # Default pulse isn't getting full 180 degrees
    s.min()
    sleep(0.5)
    s.value = 0.9
    sleep(0.5)
    s.close()  # Close it so it doesn't rattle in there - this is also the problem with the camera interfering :/

    led.on()
    with io.BytesIO() as stream:
        camera = Picamera2()
        camera.configure(camera.create_still_configuration(main={"size": (720, 480)}))
        camera.start()
        camera.capture_file(stream, format='jpeg')
        camera.close()
        bytes = stream.getvalue()
    led.off()
    return bytes
