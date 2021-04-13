import datetime
import flask_cors
import flask_limiter
import gpiozero
import io
import os
import pathlib
import redis
import rq
import subprocess
import uuid
from flask import Flask
from flask import request
from flask import send_file
from time import sleep
from werkzeug.middleware.proxy_fix import ProxyFix

from tasks.process_image import process_image
from tasks.roll_and_take_image import roll_and_take_image

app = Flask(__name__)
flask_cors.CORS(app)
if bool(os.getenv('FLASK_REVERSE_PROXY')):
    # Use this if you're using a reverse-proxy to get real IPs
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
limiter = flask_limiter.Limiter(
    app,
    key_func=flask_limiter.util.get_remote_address,
    default_limits=["10/second"],
    headers_enabled=True,
)
# Premium users who can spam as much as they want
# That is - me :)
premium_passwords = []
_p_pass_file = pathlib.Path('premium_passwords.txt')
if _p_pass_file.exists():
    with open(_p_pass_file, 'r') as f:
        premium_passwords = f.read().split()

API1 = '/api/'

_redis = redis.Redis()
queue_images = rq.Queue('images', connection=_redis)
queue_vision = rq.Queue('vision', connection=_redis)


@app.route(API1)
def hello():
    return "Hello there!"


@limiter.request_filter
def password_whitelist():
    return request.headers.get('pwd') in premium_passwords


def _roll_rate_limit():
    c = queue_vision.deferred_job_registry.count
    return ('8/minute' if c < 4 else ('4/minute' if c < 30 else '1/minute')) + ';' + \
           ('120/hour' if c < 8 else ('60/hour' if c < 30 else '30/hour'))


@app.route(API1 + 'roll/')
@limiter.limit(_roll_rate_limit())
def roll():
    image_job = queue_images.enqueue(roll_and_take_image, job_timeout='15s', result_ttl='60s', ttl='5h')
    vision_job = queue_vision.enqueue(process_image, depends_on=image_job, job_timeout='2m', result_ttl='5m', ttl='5h')
    return vision_job.id


@app.errorhandler(429)
def rate_limit_handle(e):
    return f"Rate limit exceeded :/ " + \
           ("API under heavy load 0_0 " if queue_vision.deferred_job_registry.count > 30 else '') + \
           "try again later: {e}", 429


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
        ttl = job.result['finished_time'] + job.result_ttl
    elif status in ["EXPIRED", "FAILED"]:
        ttl = 0.0
    else:
        ttl = -1.0
    return {
        'status': status,
        'queue': left,
        # IDEA: Some dynamically calculated eta, perhaps if we had multiple workers...
        # 4.56 is average time from my calculations
        'eta': (datetime.datetime.now() + datetime.timedelta(seconds=left * 4.56)).timestamp(),
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


@app.route(API1 + 'anal-image/<uuid:job_id>/')
def anal_image(job_id):
    id = str(job_id)
    job = queue_vision.fetch_job(id)
    return _handle_status(
        job,
        lambda: send_file(
            io.BytesIO(job.result['kp_image']),
            mimetype='image/jpeg',
            attachment_filename=f'{id}.jpg'
        )
    )


if __name__ == '__main__':
    if bool(os.getenv('ROLL_PRODUCTION')):
        print('Production mode...')
        # This requires to "pip install bjoern"
        # However, I didn't add it to requirements.txt, because it broke without "apt install libev-dev"
        import bjoern

        print('Running bjoern server')
        bjoern.run(app, "0.0.0.0", 5000)
    else:
        print('Dev mode...')
        os.environ['FLASK_ENV'] = 'development'
        print('Running flask dev server')
        app.run(host='0.0.0.0', port=5000, debug=True)
