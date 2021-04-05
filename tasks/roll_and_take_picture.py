import gpiozero
import subprocess
from time import sleep

led = gpiozero.LED(4)


def roll_and_take_picture():
    s = gpiozero.Servo(14, min_pulse_width=1 / 2000)  # Default pulse isn't getting full 180 degrees
    s.min()
    sleep(0.5)
    s.value = 0.9
    sleep(0.5)
    s.close()  # Close it so it doesn't rattle in there

    led.on()
    # This tells raspistill to output image to stdout, which we capture in binary form
    # This allows us to store everything in ram instead of disk
    res = subprocess.run(f'raspistill -o -'.split(), capture_output=True)
    led.off()
    return res.stdout
