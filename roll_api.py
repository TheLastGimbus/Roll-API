import gpiozero
import io
import os
import pathlib
import redis
import rq
import subprocess
import uuid
from flask import Flask
from flask import send_file
from time import sleep
from werkzeug.middleware.proxy_fix import ProxyFix

from tasks.process_image import process_image
from tasks.roll_and_take_image import roll_and_take_image

app = Flask(__name__)
if bool(os.getenv('FLASK_REVERSE_PROXY')):
    # Use this if you're using a reverse-proxy to get real IPs
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

API1 = '/api/v1/'

_redis = redis.Redis()
queue_images = rq.Queue('images', connection=_redis)
queue_vision = rq.Queue('vision', connection=_redis)


@app.route(API1)
def hello():
    return "Hello there!"


@app.route(API1 + 'roll/')
def roll():
    image_job = queue_images.enqueue(roll_and_take_image)
    vision_job = queue_vision.enqueue(process_image, depends_on=image_job)
    return vision_job.id


@app.route(API1 + 'image/<uuid:image_id>/')
def image(image_id):
    id = str(image_id)
    job = queue_vision.fetch_job(id)
    if job is None:
        return "EXPIRED", 410
    elif job.get_status() == "finished":
        return send_file(io.BytesIO(job.result), mimetype='image/jpeg', attachment_filename=f'{id}.jpg')
    elif job.get_status() == "failed":
        return "Your request was failed - I messed something up, sorry :(", 500
    elif job.get_status() == "started":
        return "RUNNING"
    elif job.get_status() in ["queued", "deferred"]:
        return "QUEUED"
