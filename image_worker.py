import gpiozero
import io
import subprocess
from picamera2 import Picamera2
from time import sleep
import rq
import sys

with rq.Connection():
    qs = sys.argv[1:] or ['images']
    w = rq.Worker(qs)
    w.work(with_scheduler=True)
