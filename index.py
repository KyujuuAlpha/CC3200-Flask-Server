from pacman import connect
from pacman import change_shadow_value

from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/left')
def leftClick():
    change_shadow_value("left")
    return ("nothing")

@app.route('/right')
def rightClick():
    change_shadow_value("right")
    return ("nothing")

@app.route('/up')
def upClick():
    change_shadow_value("up")
    return ("nothing")

@app.route('/down')
def downClick():
    change_shadow_value("down")
    return ("nothing")

connect()
