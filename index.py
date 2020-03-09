from shadow import connect
from shadow import change_shadow_value

from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/enemy', methods=['POST'])
def enemy():
    if request.method == 'POST':
        change_shadow_value("enemy_dir", request.form['direction'])
    return ("nothing")

connect()
