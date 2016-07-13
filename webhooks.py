from flask_hookserver import Hooks
import signal
import flask
import os

class WebhookHandler(object):

    def __init__(self, key):
        self.app = flask.Flask(__main__)
        self.app.config["GITHUB_WEBHOOKS_KEY"] = key
        self.hooks = Hooks(self.app, url="/")

    def run(self):
        self.app.run(host="0.0.0.0", port=8613)

    @self.hooks.hook("push")
    def push(self, data, delivery):
        print("Got push from GitHub.")
        print("Updating bot.")
        os.system("git pull")
        print("Bot updated. Sending SIGINT.")
        os.kill(os.getpid(), signal.SIGINT)
