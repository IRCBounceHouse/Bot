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
    bot.manager.rooms_notice(event.source.nick, args)

@utils.add_cmd(command="global", perms="admin")
def globalnotice(bot, event, args):
    if args == "":
        bot.reply(event, "!global <message>")
        return
    bot.manager.global_notice(event.source.nick, args)

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

@utils.add_cmd(perms="admin")
def netadd(bot, event, args):
    if args == "":
        bot.reply(event, "!netadd <name>")
        return
    name = args.split()[0]
    if bot.manager.networkdb.get_net_by_name(name):
        bot.reply(event, "Error: A network with that name already exists")
        return
    bot.manager.networkdb.addnet(name)

@utils.add_cmd(perms="admin")
def netaddsrv(bot, event, args):
    if len(args.split(" ")) < 2:
        bot.reply(event, "!netaddsrv <network> <server>")
        return
    args = args.split(" ")
    netname = args[0]
    server = args[1]
    if bot.manager.networkdb.get_net_by_server(server):
        bot.reply(event, "Error: That server already exists")
        return
    net = bot.manager.networkdb.get_net_by_name(netname)
    if not net:
        bot.reply(event, "Error: That network does not exist")
        return
    bot.manager.networkdb.addserver(net["id"], server)

@utils.add_cmd(perms="admin")
def netdefault(bot, event, args):
    if len(args.split(" ")) < 3:
        bot.reply(event, "!netdefault <network> <server> [+]<port>")
        return
    args = args.split(" ")
    netname = args[0]
    server = args[1]
    port = args[2]
    net = bot.manager.networkdb.get_net_by_name(netname)
    if not net:
        bot.reply(event, "Error: invalid network")
        return
    try:
        int(port.replace("+", "", 1))
    except ValueError:
        bot.reply(event, "Error: invalid port")
        return
    if not bot.manager.networkdb.defaultadd(net["id"], server, port):
        bot.reply(event, "Error: server already exists")

@utils.add_cmd(perms="admin")
def netsuspend(bot, event, args):
    if len(args.split(" ")) < 5:
        bot.reply(event, "!netsuspend <network> <time> "
            "<minute(s)|hour(s)|day(s)|month(s)> <type> <reason>")
        bot.reply(event, "Example: !netsuspend freenode 7 days session We are "
            "currently hitting connection limits for this network")
        return
    timeunits = ["minute", "minutes", "hour", "hours", "day", "days",
        "month", "months"]
    netname, time, unit, stype, reason = args.split(" ", 4)
    try:
        int(time)
    except ValueError:
        bot.reply(event, "Error: <time> should be an integer")
        return
    if unit not in timeunits:
        bot.reply(event, "Error: invalid unit of time")
        return
    net = bot.manager.networkdb.get_net_by_name(netname)
    if not name:
        bot.reply(event, "Error: invalid network")
        return
    time = " ".join([time, unit])
    stype = stype.upper()
    bot.manager.networkdb.suspend(net["id"], stype, reason, time)
    notice = []
    if int(net["suspended"]) > 0:
        notice.append("The suspension on the \x02{0}\x02 network has been \x02REVISED\x02.".format(net["name"]))
    else:
        notice.append("The \x02{0}\x02 network is now \x02SUSPENDED\x02".format(net["name"]))
    notice.append("\x02Reason\x02: \x02{0}\x02 issues: \x02{1}\x02".format(stype, reason))
    notice.append("\x02Duration\x02: \x02{0}\x02".format(time))
    bot.manager.bot_notice(" ".join(notice))

@utils.add_cmd(perms="admin")
def netunsuspend(bot, event, args):
    if args == "":
        bot.reply(event, "!netunsuspend <network>")
        return
    netname = args.split()[0]
    net = bot.manager.networkdb.get_net_by_name(netname)
    if not net:
        bot.reply(event, "Error: invalid network")
        return
    if net["suspended"] == 0:
        bot.reply(event, "Error: network is not suspended")
        return
    bot.manager.networkdb.unsuspend(net["id"])
    notice = "The suspension on the \x02{0}\x02 network has been \x02CANCELLED\x02.".format(net["name"])
    bot.manager.bot_notice(notice)

@utils.add_cmd(perms="admin")
def netban(bot, event, args):
    if len(args.split(" ")) < 3:
        bot.reply(event, "!netban <network> <type> <reason>")
        bot.reply(event, "Example: !netban freenode abuse Continued abuse")
        return
    netname, btype, reason = args.split(" ", 2)
    net = bot.manager.networkdb.get_net_by_name(netname)
    if not net:
        bot.reply(event, "Error: invalid network")
        return
    if net["banned"] > 0:
        bot.reply(event, "Error: network is already banned")
        return
    btype = btype.upper()
    bot.manager.networkdb.ban(net["id"], btype, reason)
    notice = []
    notice.append("The \x02{0}\x02 network is now \x02BANNED\x02.".format(net["name"]))
    notice.append("\x02Reason\x02: \x02{0}\x02 issues: \x02{1}\x02".format(btype, reason))
    bot.manager.bot_notice(" ".join(notice))

@utils.add_cmd(perms="admin")
def netunban(bot, event, args):
    if args == "":
        bot.reply(event, "!netunban <network>")
        return
    netname = args.split()[0]
    net = bot.manager.networkdb.get_net_by_name(netname)
    if not net:
        bot.reply(event, "Error: invalid network")
        return
    if net["banned"] == 0:
        bot.reply(event, "Error: network is not banned")
        return
    bot.manager.networkdb.unban(net["id"])
    notice = "The ban on the \x02{0}\x02 network has been \x02CANCELLED\x02.".format(net["name"])
    bot.manager.bot_notice(notice)

@utils.add_cmd(perms="admin")
def adduser(bot, event, args):
    "!adduser Aegir TestUser freenode"
    if len(args.split(" ")) < 3:
        bot.reply(event, "!adduser <server> <username> <network>")
        return
    args = args.split(" ")
    server = args[0]
    username = args[1]
    network = args[2]
    for name in bot.manager.connections["znc"]:
        if name.lower() == server.lower()
            server = name
            break
    else:
        bot.reply(event, "Error: invalid server")
        return
    net = bot.manager.networkdb.get_net_by_name(network)
    if not net:
        bot.reply(event, "Error: invalid network")
        return
    servers = bot.manager.get_net_defaults(net["id"])
    if not servers:
        bot.reply(event, "Error: no servers for network")
        return
    passwd = utils.genpasswd()
    bot.manager.add_user(server, username, passwd)
    bot.manager.add_net(server, username, net["name"])
    for srv in servers:
        bot.manager.add_server(server, username, network, srv["address"], srv["port"])

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
