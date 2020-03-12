from aws_shadow import connect
from aws_shadow import changeShadowValue
from aws_shadow import getSubscribedPropertyVal
from aws_shadow import selectBaddie
from aws_shadow import queueMovement

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
        queueMovement(request.form['direction'])
    return ("nothing")

@app.route('/select', methods=['POST'])
def select():
    if request.method == 'POST':
        selectBaddie(int(request.form['control']))
    return ("nothing")

@app.route('/loc', methods=['POST'])
def loc():
    if request.method == 'POST':
        changeShadowValue("b" + request.form['b'] + "_loc", request.form['x'] + " " + request.form['y'])
    return ("nothing")

@app.route('/api')
def api_page():
    return {
        "pac_loc": getSubscribedPropertyVal("pac_loc"),
        "b1_loc": getSubscribedPropertyVal("b1_loc"),
        "b2_loc": getSubscribedPropertyVal("b2_loc"),
        "b3_loc": getSubscribedPropertyVal("b3_loc"),
        "b4_loc": getSubscribedPropertyVal("b4_loc"),
        "b1_q": getSubscribedPropertyVal("b1_q"),
        "b2_q": getSubscribedPropertyVal("b2_q"),
        "b3_q": getSubscribedPropertyVal("b3_q"),
        "b4_q": getSubscribedPropertyVal("b4_q")
    }

connect()
