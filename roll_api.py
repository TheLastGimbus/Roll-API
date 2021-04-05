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

from tasks.roll_and_take_picture import roll_and_take_picture

app = Flask(__name__)
if bool(os.getenv('FLASK_REVERSE_PROXY')):
    # Use this if you're using a reverse-proxy to get real IPs
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

API1 = '/api/v1/'

queue = rq.Queue(connection=redis.Redis())


@app.route(API1)
def hello():
    return "Hello there!"


@app.route(API1 + 'roll/')
def roll():
    job = queue.enqueue(roll_and_take_picture)
    # TODO: Recognize dice
    return job.id


@app.route(API1 + 'image/<uuid:image_id>/')
def image(image_id):
    id = str(image_id)
    job = queue.fetch_job(id)
    return send_file(io.BytesIO(job.result), mimetype='image/jpeg', attachment_filename=f'{id}.jpg')
