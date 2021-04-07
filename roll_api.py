import flask_limiter
import gpiozero
import io
import os
import pathlib
import redis
import rq
import subprocess
import uuid
from datetime import datetime
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
limiter = flask_limiter.Limiter(
    app,
    key_func=flask_limiter.util.get_remote_address,
    default_limits=["10/second"]
)

API1 = '/api/'

_redis = redis.Redis()
queue_images = rq.Queue('images', connection=_redis)
queue_vision = rq.Queue('vision', connection=_redis)


@app.route(API1)
def hello():
    return "Hello there!"


@app.route(API1 + 'roll/')
@limiter.limit("4/minute")
@limiter.limit("60/hour")
def roll():
    image_job = queue_images.enqueue(roll_and_take_image, job_timeout='15s', result_ttl='60s')
    vision_job = queue_vision.enqueue(process_image, depends_on=image_job, job_timeout='2m', result_ttl='5m')
    return vision_job.id


@app.errorhandler(429)
def rate_limit_handle(e):
    return f"Rate limit exceeded :/ try again later: {e}", 429


def _handle_status(job, finished_func):
    if job is None:
        return "EXPIRED", 410
    elif job.get_status() == "finished":
        return finished_func(), 200
    elif job.get_status() == "failed":
        return "FAILED", 500
    elif job.get_status() == "started":
        return "RUNNING", 201
    elif job.get_status() in ["queued", "deferred"]:
        return "QUEUED", 202


@app.route(API1 + 'info/<uuid:job_id>/')
def info(job_id):
    job_id = str(job_id)
    job = queue_vision.fetch_job(job_id)  # Can be None
    # How many jobs are in queue before you
    r = queue_vision.deferred_job_registry
    all_jobs = r.get_job_ids()
    try:
        index = all_jobs.index(job_id)
        left = len(r.get_job_ids(end=index))
    except ValueError:
        left = 0
    # This will nicely handle None-checking etc and return you the status in string
    status = _handle_status(job, lambda: "FINISHED")[0]
    # How much time has left for results to be available
    if status == "FINISHED":
        ttl = int(job.result_ttl - (datetime.now().timestamp() - job.result['finished_time']))
    elif status in ["EXPIRED", "FAILED"]:
        ttl = 0
    else:
        ttl = -1
    return {
        'status': status,
        'queue': left,
        # IDEA: Some dynamically calculated eta, perhaps if we had multiple workers...
        'eta': left * 4.56,  # 4.56 is average time from my calculations
        'ttl': ttl,
        'result': None if status != "FINISHED" else job.result['number']
    }


@app.route(API1 + 'result/<uuid:job_id>/')
def result(job_id):
    job = queue_vision.fetch_job(str(job_id))
    return _handle_status(
        job,
        lambda: str(job.result['number'])
    )


@app.route(API1 + 'image/<uuid:job_id>/')
def image(job_id):
    id = str(job_id)
    job = queue_vision.fetch_job(id)
    return _handle_status(
        job,
        lambda: send_file(
            io.BytesIO(job.result['original_image']),
            mimetype='image/jpeg',
            attachment_filename=f'{id}.jpg'
        )
    )
