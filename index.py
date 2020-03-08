from pacman import connect
from pacman import change_shadow_value

from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/click')
def click():
    change_shadow_value("hello2")
    return ("nothing")

connect()
