from shadow import connect
from shadow import change_shadow_value
from shadow import get_subscribed_value

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
        change_shadow_value("bad_dir", request.form['direction'])
    return ("nothing")

@app.route('/api')
def api_page():
    return {
        "pac_loc": get_subscribed_value("pac_loc"),
        "b1_loc": get_subscribed_value("b1_loc"),
        "b2_loc": get_subscribed_value("b2_loc"),
        "b3_loc": get_subscribed_value("b3_loc"),
        "b4_loc": get_subscribed_value("b4_loc"),
    }

connect()
