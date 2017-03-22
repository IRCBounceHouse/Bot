import code
import sys

import utils

@utils.add_cmd(perms="admin")
def reload(bot, event, args):
    bot.reply(event, "Reloading plugins...")
    bot.manager.reloadplugins()
    bot.reply(event, "Reloaded.")

@utils.add_cmd(perms="admin")
def pending(bot, event, args):
    reqs = bot.manager.requestdb.get_pending()
    if not reqs:
        bot.reply(event, "No requests are currently pending")
        return
    for req in reqs:
        reqdata = []
        reqdata.append("\x02ID\x02: \x02{0}\x02".format(req["id"]))
        reqdata.append("\x02Username\x02: \x02{0}\x02".format(req["username"]))
        reqdata.append("\x02Email\x02: \x02{0}\x02".format(req["email"]))
        reqdata.append("\x02Source\x02: \x02{0}\x02".format(req["source"]))
        bot.reply(event, ", ".join(reqdata))

@utils.add_cmd(perms="admin")
def accept(bot, event, args):
    if len(args.split(" ")) < 1:
        bot.reply(event, "!accept <id>")
        return
    args = args.split(" ")
    reqid = args[0]
    req = bot.manager.requestdb.get_by_id(reqid)
    if not req:
        bot.reply(event, "Error: invalid request ID")
        return
    if req["status"] != "pending":
        bot.reply(event, "Error: you may only accept pending requests")
        return
    bot.manager.requestdb.accept(req["id"], event.source.nick)
    passwd = utils.genpasswd()
    bot.msg("*controlpanel", "AddUser {0} {1}".format(req["username"], passwd))
    bot.msg("*controlpanel", "Set MaxNetworks {0} 10".format(req["username"]))
    bot.msg("*controlpanel", "Set DenySetBindHost {0} true".format(req["username"]))
    bot.manager.mail.accept(req["email"], req["username"], passwd)
    bot.msg("#IRCBounceHouse", "\x02\x033Request ACCEPTED\x0f. \x02Username\x02: \x02{0}\x02".format(req["username"]))

@utils.add_cmd(perms="admin")
def reject(bot, event, args):
    if len(args.split(" ")) < 2:
        bot.reply(event, "!reject <id> <reason>")
        return
    reqid, reason = args.split(" ", 1)
    req = bot.manager.requestdb.get_by_id(reqid)
    if not req:
        bot.reply(event, "Error: invalid request ID")
        return
    if req["status"] != "pending":
        bot.reply(event, "Error: you may only reject pending requests")
        return
    bot.manager.requestdb.reject(req["id"], event.source.nick, reason)
    bot.manager.mail.reject(req["email"], reason)
    bot.msg("#IRCBounceHouse", "\x02\x034Request REJECTED\x0f. \x02Username\x02: \x02{0}\x02, \x02Reason\x02: \x02{1}\x02".format(req["username"], reason))

@utils.add_cmd(perms="admin")
def deluser(bot, event, args):
    if len(args.split(" ")) < 1:
        bot.reply(event, "!deluser <username>")
    username = args[0]
    c = self.db.cursor()
    c.execute("""UPDATE requests SET status = "deleted", decided_at = CURRENT_TIMESTAMP,decided_by = ? WHERE username = ?""", (source, username))
    c.close()
    bot.msg("*controlpanel", "DelUser {0}".format(req["username"]))
    bot.msg("#IRCBounceHouse-dev", "\x02Username {0} deleted!".format(req["username"]))

@utils.add_cmd(perms="admin")
def release(bot, event, args):
    if len(args.split(" ")) < 1:
        bot.reply(event, "!release <username>")
    username = args[0]
    c = self.db.cursor()
    c.execute("""DELETE FROM requests WHERE username = ?""", (username))
    c.close()
    bot.msg("#IRCBounceHouse-dev", "\x02Username {0} released!".format(req["username"]))

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
