from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config.from_object('config')

thing_name = "CC3200_Thing"
shadow_property = "var"
endpoint = "a1euv4eww1wx8z-ats.iot.us-west-2.amazonaws.com"
client_id = "Web-Client-1.0"
signing_region = "us-west-2"

cert = "cert/client.pem"
key = "cert/private.pem"
root_ca = "cert/ca.pem"

@app.route('/')
def index():
    return render_template("index.html")
