from fnmatch import fnmatch
import importlib
import threading
import traceback
import socket
import glob
import json
import time
import ssl
import sys
import os

from mail import Mail
import databases
import webhooks
import utils

class BNCBotManager(object):

    def __init__(self, conf):
        self.config = conf
        self.connections = {
            "irc": {},
            "znc": {}
        }
        self.threads = []
        self.plugins = {}
        self.events = []
        self.mtimes = {}
        print("Loading plugins")
        self.reloadplugins()
        self.mail = Mail(self.config["smtp"])
        self.requestdb = databases.RequestDB()
        self.networkdb = databases.NetworkDB()
        self.verifydb = databases.VerifyDB()
        for name, server in self.config["irc"].items():
            bot = self.BNCBot(
                name=name,
                conntype="IRC",
                host=self.config["zncaddr"],
                port=self.config["zncport"],
                user="bot/{0}".format(name),
                passwd=self.config["zncpass"],
                use_ssl=self.config["zncssl"],
                conf=server
            )
            self.connections["irc"][name] = bot
            if server.get("admin"):
                self.adminbot = bot
        for name, server in self.config["znc"].items():
            self.connections["znc"][name] = self.BNCBot(
                name=name,
                conntype="ZNC",
                host=server["host"],
                port=server["port"],
                user=server["user"],
                passwd=server["pass"],
                use_ssl=server["ssl"],
                conf=server
            )
        for name, bot in self.connections["irc"].items():
            print("Starting IRC connection to {0}".format(name))
            t = threading.Thread(target=bot.run, args=(self,))
            t.daemon = True
            t.start()
            self.threads.append(t)
        for name, bot in self.connections["znc"].items():
            print("Starting ZNC connection to {0}".format(name))
            t = threading.Thread(target=bot.run, args=(self,))
            t.daemon = True
            t.start()
            self.threads.append(t)
        print("All connections started.")
        try:
            for thread in self.threads:
                thread.join()
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt. Shutting down gracefully.")
            for conntype in self.connections.values():
                for bot in conntype.values():
                    bot.quit("Caught KeyboardInterrupt")
            sys.exit(1)

    def importplugin(self, plugin_name, path, reload=False):
        try:
            self.plugins[plugin_name] = importlib.import_module(plugin_name)
            if reload:
                utils.events = []
                self.plugins[plugin_name] = importlib.reload(self.plugins[plugin_name])
        except:
            print("Unable to (re)load {0}:".format(plugin_name))
            traceback.print_exc()
        self.mtimes[plugin_name] = os.path.getmtime(path)

    def reloadplugins(self):
        for plugin in glob.glob(os.path.join(os.getcwd(), "plugins", "*.py")):
            import_name = "plugins.{0}".format(plugin.split(os.path.sep)[-1][:-3])
            if import_name in self.mtimes.keys():
                if os.path.getmtime(plugin) != self.mtimes[import_name]:
                    utils.events = []
                    self.importplugin(import_name, plugin, True)
                    for command in utils.events:
                        print("New command found: {0}".format(command.__name__))
                        utils.events[utils.events.index(command)].__module__ = import_name
                        for cmd in [e for e in self.events if e.__module__ == import_name]:
                            if ((utils.events[utils.events.index(command)].__name__ == cmd.__name__) or
                            (cmd.__module__ == import_name and cmd.__name__ not in [e.__name__ for e in utils.events])):
                                print("Deleting an old command: {0}".format(cmd.__name__))
                                del(self.events[self.events.index(cmd)])
                    print("Reloaded plugin: {0}".format(str(plugin)))
                    self.events = utils.events + self.events
            else:
                utils.events = []
                self.importplugin(import_name, plugin)
                for command in utils.events:
                    print("New command found: {0}".format(command.__name__))
                    utils.events[utils.events.index(command)].__module__ = import_name
                print("New plugin: {0}".format(str(plugin)))
                self.events = utils.events + self.events

    def global_notice(self, source, msg):
        msgtext = "[\x02GLOBAL NOTICE\x02] (from \x02{0}\x02) {1}".format(source, msg)
        for bot in self.connections["irc"].values():
            bot.msg("#SuperBNC", msgtext)
        for bot in self.connections["znc"].values():
            bot.msg("*status", "broadcast {0}".format(msgtext))

    def rooms_notice(self, source, msg):
        msgtext = "[\x02ROOMS NOTICE\x02] (from \x02{0}\x02) {1}".format(source, msg)
        for bot in self.connections["irc"].values():
            bot.msg("#SuperBNC", msgtext)

    def bot_notice(self, msg):
        msgtext = "[\x02BOT NOTICE\x02] {0}".format(msg)
        for bot in self.connections["irc"].values():
            bot.msg("#SuperBNC", msgtext)

    def add_user(self, server, username, password):
        if server not in self.connections["znc"]:
            return False
        self.connections["znc"][server].msg("*controlpanel", "AddUser {0} {1}".format(
            username, password))
        return True

    def add_net(self, server, username, network):
        if server not in self.connections["znc"]:
            return False
        self.connections["znc"][server].msg("*controlpanel", "AddNetwork {0} {1}".format(
            username, network))
        if network in self.connections["irc"]:
            self.connections["znc"][server].msg("*controlpanel",
                "AddChan {0} {1} #SuperBNC".format(username, network))
        return True

    def add_server(self, server, username, network, host, port):
        if server not in self.connections["znc"]:
            return False
        self.connections["znc"][server].msg("*controlpanel",
            "AddServer {0} {1} {2} {3}".format(username, network, host, port))
        return True

    class BNCBot(object):

        def __init__(self, name, conntype, host, port, user, passwd, use_ssl, conf):
            self.name = name
            self.type = conntype
            self.host = host
            self.port = port
            self.user = user
            self.passwd = passwd
            self.ssl = use_ssl
            self.connected = False
            self.config = conf
            self.down = False
            self.debug = False

        def run(self, manager):
            self.manager = manager
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.ssl:
                self.socket = ssl.wrap_socket(self.socket)
            try:
                self.socket.connect((self.host, self.port))
                if self.down:
                    self.down = False
                    self.manager.adminbot.msg("#SuperBNC-Staff",
                        "\x02Connected\x02: \x02{0}\x02 (\x02Socket\x02)".format(self.name))
                    if self.type == "ZNC":
                        self.manager.bot_notice(
                            "The \x02{0}\x02 server appears to be back \x02\x033UP\x0f.".format(self.name))
                self.connected = True
            except socket.error:
                self.handle_disconnect(send_notice=False)
            self.send("PASS {0}".format(self.passwd))
            self.send("USER {0} * * :{0}".format(self.user))
            self.send("NICK {0}".format(self.user))
            self.loop()

        def send(self, text):
            if self.connected:
                self.socket.send("{0}\r\n".format(text).encode())
                if self.debug:
                    print("[SEND][{0}]({1}) {2}".format(self.type, self.name, text))

        def recv(self):
            part = ""
            data = ""
            while not part.endswith("\r\n"):
                part = self.socket.recv(2048)
                part = part.decode()
                data += part
            return data.splitlines()

        def quit(self, message=None):
            if message:
                self.send("QUIT :{0}".format(message))
            else:
                self.send("QUIT")

        def msg(self, target, msg):
            self.send("PRIVMSG {0} :{1}".format(target, msg))

        def reply(self, event, msg):
            if event.target.startswith("#"):
                replyto = event.target
            else:
                replyto = event.source.nick
            self.msg(replyto, msg)

        def join(self, channel, key=None):
            if key:
                self.send("JOIN {0} {1}".format(channel, key))
            else:
                self.send("JOIN {0}".format(channel))

        def part(self, channel, msg=None):
            if msg:
                self.send("PART {0} :{1}".format(channel, msg))
            else:
                self.send("PART {0}".format(channel))

        def mode(self, channel, modes):
            self.send("MODE {0} {1}".format(channel, modes))

        def kick(self, channel, nick, msg=None):
            if msg:
                self.send("KICK {0} {1} :{2}".format(channel, nick, msg))
            else:
                self.send("KICK {0} {1}".format(channel, nick))

        def remove(self, channel, nick, msg=None):
            if msg:
                self.send("REMOVE {0} {1} :{2}".format(channel, nick, msg))
            else:
                self.send("REMOVE {0} {1}".format(channel, nick))

        def handle_disconnect(self, send_notice=True):
            self.connected = False
            self.down = True
            print("{0} connection to {1} died, reconnecting...".format(self.type.upper(), self.name))
            if send_notice:
                self.manager.adminbot.msg("#SuperBNC-Staff",
                    "\x02Disconnect detected\x02: \x02{0}\x02 (\x02Socket\x02)".format(self.name))
                if self.type == "ZNC":
                    self.manager.bot_notice("The \x02{0}\x02 server appears to be \x02\x034DOWN\x0f.".format(self.name))
            time.sleep(10)
            self.run(self.manager)

        def loop(self):
            while True:
                try:
                    data = self.recv()
                except socket.error:
                    self.handle_disconnect()
                for line in data:
                    self.manager.requestdb.expires()
                    self.manager.networkdb.expires()
                    self.manager.verifydb.expires()
                    event = Event(line)
                    t = threading.Thread(target=self.handle_event, args=(event,))
                    t.daemon = True
                    t.start()
                    for func in [e for e in self.manager.events if e._event == "trigger"]:
                        if e._trigger.upper() == event.type or e._trigger.upper() == "ALL":
                            t = threading.Thread(target=func, args=(self, event))
                            t.daemon = True
                            t.start()
                    if self.debug:
                        print("[RECV][{0}]({1}) {2}".format(self.type, self.name, line))

        def handle_event(self, event):
            if event.type == "PING":
                self.send("PONG :{0}".format(event.arguments[0]))
            elif event.type == "PONG":
                self.lastping = time.time()
            elif event.type == "001":
                self.lastping = time.time()
                self.ping_thread = threading.Thread(target=self.ping)
                self.ping_thread.daemon = True
                self.ping_thread.start()
            elif event.type == "PRIVMSG":
                if str(event.source) == "*status!bnc@superbnc.com":
                    if event.arguments[0].startswith("Disconnected from IRC.") and not self.down:
                        self.down = True
                        self.manager.adminbot.msg("#SuperBNC-Staff",
                            "\x02Disconnect detected\x02: \x02{0}\x02 (\x02ZNC\x02)".format(self.name))
                    elif event.arguments[0] == "Connected!" and self.down:
                        self.down = False
                        self.manager.adminbot.msg("#SuperBNC-Staff",
                            "\x02Connected\x02: \x02{0}\x02 (\x02ZNC\x02)".format(self.name))
                if len(event.arguments[0].split(" ")) > 1:
                    command, args = event.arguments[0].split(" ", 1)
                else:
                    command = event.arguments[0]
                    args = ""
                self.handle_command(command, event, args)

        def ping(self):
            while self.connected:
                diff = time.time() - self.lastping
                if diff > 90:
                    self.quit("Lag: {0} seconds".format(int(diff)))
                else:
                    self.send("PING :{0}".format(time.time()))
                sleep(30)

        def handle_command(self, command, event, args):
            for func in [e for e in self.manager.events if e._event == "command"]:
                if (func._prefix+func._cmdname).lower() == command.lower() or (
                func._cmdname.lower() == command.lower() and not event.target.startswith("#")):
                    if self.hasperm(func._perms, event.source) or func._perms == "all":
                        if event.target.startswith("#"):
                            chan = event.target
                        else:
                            chan = "private"
                        if len(args) > 0:
                            commandargs = " ".join([command, args])
                        else:
                            commandargs = command
                        print("({0}) {1} called {2} in {3}".format(
                            self.name, event.source, repr(commandargs), chan))
                        func(self, event, args)

        def hasperm(self, perm, mask):
            for perm_mask in self.config.get("perms", {}).get(perm, []):
                if fnmatch(str(mask), perm_mask):
                    return True
            return False

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

if __name__ == "__main__":
    with open("config.json") as configfile:
        config = json.load(configfile)
    if not os.path.exists(os.path.join(os.getcwd(), "data")):
        os.mkdir(os.path.join(os.getcwd(), "data"))
    webhooks.app.config["GITHUB_WEBHOOKS_KEY"] = config["github_secret"]
    t = threading.Thread(target=webhooks.app.run, args=("0.0.0.0", 8163))
    t.daemon = True
    t.start()
    manager = BNCBotManager(config)
