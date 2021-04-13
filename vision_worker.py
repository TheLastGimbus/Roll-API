import cv2  # This takes SUPER long on my Pi Zero 0_o
import numpy as np
import rq
import sys

with rq.Connection():
    qs = sys.argv[1:] or ['vision']
    w = rq.Worker(qs)
    w.work(with_scheduler=True)
