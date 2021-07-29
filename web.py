from flask import Flask
import settings

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>HELLO</h1>'


def run():
    app.run(debug=settings.FLASK_DEBUG, host='0.0.0.0', port=5000)