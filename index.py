from aws_shadow import connect
from aws_shadow import changeShadowValue
from aws_shadow import getSubscribedPropertyVal

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
        changeShadowValue("bad_dir", request.form['direction'])
    return ("nothing")

@app.route('/select', methods=['POST'])
def enemy():
    if request.method == 'POST':
        changeShadowValue("bad_ctrl", request.form['control'])
    return ("nothing")


@app.route('/api')
def api_page():
    return {
        "pac_loc": getSubscribedPropertyVal("pac_loc"),
        "b1_loc": getSubscribedPropertyVal("b1_loc"),
        "b2_loc": getSubscribedPropertyVal("b2_loc"),
        "b3_loc": getSubscribedPropertyVal("b3_loc"),
        "b4_loc": getSubscribedPropertyVal("b4_loc"),
    }

connect()
