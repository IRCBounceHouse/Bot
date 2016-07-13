import code
import sys

import utils

@utils.add_cmd(perms="admin")
def reload(bot, event, args):
    bot.reply(event, "Reloading plugins...")
    bot.manager.reloadplugins()
    bot.reply(event, "Reloaded.")

@utils.add_cmd(perms="admin")
def rooms(bot, event, args):
    if args == "":
        bot.reply(event, "!rooms <message>")
        return
    for conn in bot.manager.connections["irc"].values():
        conn.msg("#SuperBNC", "[\x02ROOMS NOTICE\x02] (from \x02{0}\x02) {1}".format(
            event.source.nick, args))

@utils.add_cmd(command="global", perms="admin")
def globalnotice(bot, event, args):
    if args == "":
        bot.reply(event, "!global <message>")
        return
    for conn in bot.manager.connections["irc"].values():
        conn.msg("#SuperBNC", "[\x02GLOBAL NOTICE\x02] (from \x02{0}\x02) {1}".format(
            event.source.nick, args))
    for conn in bot.manager.connections["znc"].values():
        conn.msg("*status", "broadcast [\x02GLOBAL NOTICE\x02] (from \x02{0}\x02) {1}".format(
            event.source.nick, args))

@utils.add_cmd(perms="admin")
def relay(bot, event, args):
    if len(args.split(" ")) < 2:
        bot.reply(event, "!relay <network> <message>")
        return
    net, msg = args.split(" ", 1)
    for name, irc in bot.manager.connections["irc"].items():
        if name.lower() == net.lower():
            irc.msg("#SuperBNC", "Relayed message from \x02{0}\x02: {1}".format(
                event.source.nick, msg))
            break

@utils.add_cmd(command=">>", perms="admin")
def pyeval(bot, event, args):
    pyenv = Repl({
        "bot": bot,
        "event": event
    })
    for line in pyenv.run(args).splitlines():
        if len(line) > 0:
            bot.reply(event, line)

class Repl(code.InteractiveConsole):
    '''Interractive Python Console class'''
    def __init__(self, items=None):
        if items is None:
            items = {}
        code.InteractiveConsole.__init__(self, items)
        self._buffer = ""

    def write(self, data):
        self._buffer += str(data)

    def run(self, data):
        sys.stdout = self
        self.push(data)
        sys.stdout = sys.__stdout__
        result = self._buffer
        self._buffer = ""
        return result

    def showtraceback(self):
        exc_type, value, lasttb = sys.exc_info()
        self._buffer+="{0}: {1}".format(exc_type.__name__, value)

    def showsyntaxerror(self, *args):
        self.showtraceback()
