import gpiozero
import io
import subprocess
from picamera import PiCamera
from time import sleep

led = gpiozero.LED(4)


def roll_and_take_image():
    s = gpiozero.Servo(14, min_pulse_width=1 / 2000)  # Default pulse isn't getting full 180 degrees
    s.min()
    sleep(0.5)
    s.value = 0.9
    sleep(0.5)
    s.close()  # Close it so it doesn't rattle in there

    led.on()
    with io.BytesIO() as stream:
        with PiCamera() as camera:
            camera.resolution = (720, 480)
            camera.capture(stream, 'jpeg')
        bytes = stream.getvalue()
    led.off()
    return bytes
