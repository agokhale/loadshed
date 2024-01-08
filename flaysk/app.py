import flask
import time
import loadshed

#https://flask.palletsprojects.com/en/2.0.x/quickstart/#a-minimal-application

def lol503():
     return( str(loadshed.getchannelctx()), 503)

loadshed.addchannel(channel="bob", shedding_fn=lol503, threshold_sec=1.0, cooldown_sec=10.33)
app = flask.Flask(__name__)

@app.route("/")
@loadshed.protect("bob")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/slo")
@loadshed.protect("bob")
def slo():
    time.sleep(2.02)
    return "<p>Hello, slo!</p>"

