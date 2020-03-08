from pacman import connect
from pacman import change_shadow_value

from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/enemy/<direction>')
def enemyDirection(direction):
    change_shadow_value(direction)
    return ("nothing")

connect()
