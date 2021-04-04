from flask import Flask

app = Flask(__name__)


@app.route('/api/v1')
def hello():
    return {"message": "Hello there!"}
