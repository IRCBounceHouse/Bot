from flask_hookserver import Hooks
import signal
import flask
import os

app = flask.Flask(__name__)
hooks = Hooks(app, url="/")

@hooks.hook("push")
def push(data, delivery):
    print("Got push from GitHub.")
    print("Updating bot.")
    os.system("git pull")
    print("Bot updated. Sending SIGINT.")
    os.kill(os.getpid(), signal.SIGINT)
