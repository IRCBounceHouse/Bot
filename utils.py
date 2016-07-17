import collections
import hashlib
import random
import string
import json
import os

events = []

def add_cmd(func=None, **kwargs):
    def wrapper(func):
        func._event = "command"
        func._cmdname = kwargs.get("command", func.__name__)
        func._prefix = kwargs.get("prefix", "!")
        func._perms = kwargs.get("perms", "all")
        events.append(func)
    if isinstance(func, collections.Callable):
        return wrapper(func)
    return wrapper

def add_trigger(func=None, **kwargs):
    def wrapper(func):
        func._event = "trigger"
        func._trigger = kwargs.get("trigger", "ALL")
        events.append(func)
    if isinstance(func, collections.Callable):
        return wrapper(func)
    return wrapper

def genkey():
    return hashlib.md5(os.urandom(27)).hexdigest()

def genpasswd():
    alphanumeric = string.ascii_letters + string.digits
    return "".join([random.choice(alphanumeric) for _ in range(16)])

def banmask(net, hostmask):
    nm = NickMask(hostmask)
    if net in ["freenode", "Stuxnet"]:
        if re.match("(gateway|nat|conference)/.*", nm.host):
            if "/irccloud.com/" in nm.host:
                nm.user = "*{0}".format(nm.user[1:])
            elif nm.host.startswith("gateway/web/"):
                return "*!{0}@gateway/web/*".format(nm.user)
            return "*!{0}@{1}/*".format(nm.user, "/".join(nm.host.split("/")[:-1]))
        elif "/" in nm.host:
            return "*!*@{0}".format(nm.host)
    if nm.user.startswith("~"):
        return "*!*@{0}".format(nm.host)
    return "*!{0}@{1}".format(nm.user, nm.host)

class Event(object):

    def __init__(self, raw):
        self.raw = raw
        if raw.startswith(":"):
            raw = raw.replace(":", "", 1)
            if len(raw.split(" ", 3)) > 3:
                self.source, self.type, self.target, args = raw.split(" ", 3)
            else:
                self.source, self.type, self.target = raw.split(" ", 3)
                args = ""
            self.source = NickMask(self.source)
        else:
            self.type, args = raw.split(" ", 1)
            self.source = self.target = None
        self.arguments = []
        args = args.split(":", 1)
        for arg in args[0].split(" "):
            if len(arg) > 0:
                self.arguments.append(arg)
        if len(args) > 1:
            self.arguments.append(args[1])

    def __str__(self):
        tmpl = (
            "type: {type}, "
            "source: {source}, "
            "target: {target}, "
            "arguments: {arguments}, "
            "raw: {raw}"
        )
        return tmpl.format(**vars(self))

class NickMask(object):

    def __init__(self, hostmask):
        hostmask = str(hostmask)
        if "!" in hostmask:
            self.nick, self.userhost = hostmask.split("!", 1)
            self.user, self.host = self.userhost.split("@", 1)
        else:
            self.nick = hostmask
            self.userhost = self.user = self.host = None

    def __str__(self):
        if self.userhost:
            return "{0}!{1}@{2}".format(self.nick, self.user, self.host)
        else:
            return self.nick
