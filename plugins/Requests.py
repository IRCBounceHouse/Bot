import socket
import re

import utils

@utils.add_cmd
def request(bot, event, args):
    if not event.target.startswith("#"):
        bot.reply(event, "Requests must be made in a channel.")
    if len(args.split(" ")) < 3:
        bot.reply(event, "\x02Syntax\x02: \x02!request <username> <network> <email>\x02")
        bot.reply(event, "or \x02!request <username> <irc.server> <port> <email>\x02")
        bot.reply(event, "\x02For SSL\x02: add a + before the port (e.g +6697)")
        bot.reply(event, "\x02Terms of Service\x02: https://SuperBNC.com/tos")
        bot.reply(event, "To request by email, see \x02!emailreq\x02. If the request "
            "is for this network (\x02{0}\x02), also see \x02!easyreq\x02".format(bot.name))
        return
    args = args.split(" ")
    username = args[0]
    net = bot.manager.networkdb.get_net_by_name(args[1])
    if not re.fullmatch("^[a-zA-Z][a-zA-Z@._\-]+$", username):
        bot.reply(event, "\x02Error\x02: Invalid username.")
        return
    if not net:
        if len(args) < 4:
            bot.reply(event, "\x02Error\x02: Unknown network or no port specified")
            return
        try:
            socket.getaddrinfo(args[1], None)
            server = args[1]
        except socket.gaierror:
            bot.reply(event, "\x02Error\x02: Invalid server specified")
            return
        try:
            int(args[2].replace("+", "", 1))
            port = args[2]
        except ValueError:
            bot.reply(event, "\x02Error\x02: Invalid port specified")
            return
        email = args[3]
        net = bot.manager.networkdb.get_net_by_server(args[1])
    else:
        defaults = bot.manager.networkdb.get_net_defaults(net["id"])
        if not defaults:
            bot.reply(event, "\x02Error\x02: No default server could be found")
            return
        server = defaults[0]["address"]
        port = "default"
        email = args[2]
    if net:
        if net["suspended"] > 0:
            bot.reply(event, "The \x02{0}\x02 network is \x02SUSPENDED\x02. \x02Reason\x02: "
                "\x02{1}\x02 issues: \x02{2}\x02".format(net["name"], net["suspendtype"],
                net["suspendrson"]))
            return
        if net["banned"] > 0:
            bot.reply(event, "The \x02{0}\x02 network is \x02BANNED\x02. \x02Reason\x02: "
                "\x02{1}\x02 issues: \x02{2}\x02".format(net["name"], net["bantype"],
                net["banrson"]))
            return
    if "@" not in email:
        bot.reply(event, "\x02Error\x02: Invalid email specified")
        return
    requsers = bot.manager.requestdb.get_by_user(username)
    if requsers:
        for requser in requsers:
            if requser["status"] != "rejected":
                bot.reply(event, "\x02Error\x02: There is already a request with this username")
                return
    reqemails = bot.manager.requestdb.get_by_email(email)
    if reqemails:
        for reqemail in reqemails:
            if reqemail["status"] != "rejected":
                bot.reply(event, "\x02Error\x02: There is already a request with this email")
                return
    bot.manager.requestdb.add(username, email, str(event.source), server, port, bot.name)
    thisreq = bot.manager.requestdb.get_by_email(email)[-1]
    key = utils.genkey()
    bot.manager.verifydb.add(key, "request", thisreq["id"])
    bot.manager.mail.verify(email, key)
    bot.reply(event, "\x02You have completed the first step!\x02 Please follow the instructions sent to "
        "the email address you specified to verify your request.")

@utils.add_cmd
def easyreq(bot, event, args):
    if args == "":
        bot.reply(event, "\x02Syntax\x02: \x02!easyreq <email>\x02")
        bot.reply(event, "This will make a request for this network using your current nick "
            "as the username")
        return
    email = args.split(" ")[0]
    bot.handle_command("!request", event, "{0} {1} {2}".format(event.source.nick, bot.name, email))

@utils.add_cmd
def verify(bot, event, args):
    if args == "":
        bot.reply(event, "\x02Syntax\x02: \x02!verify <key>\x02")
        return
    verifykey = args.split(" ")[0]
    key = bot.manager.verifydb.get_by_key(verifykey)
    if not key:
        bot.reply(event, "\x02Error\x02: Invalid key")
        return
    if key["command"] == "request":
        bot.manager.requestdb.verify(key["action_id"])
        req = bot.manager.requestdb.get_by_id(key["action_id"])
        bot.reply(event, "\x02Your email has now been verified!\x02 Please wait for a staff member "
            "to process your request. You can check the status of your request by using "
            "\x02!check {0}\x02".format(req["username"]))
    bot.manager.verifydb.used(verifykey)

@utils.add_cmd
def check(bot, event, args):
    if args == "":
        bot.reply(event, "\x02Syntax\x02: \x02!check <username>\x02")
        return
    username = args.split(" ")[0]
    req = bot.manager.requestdb.get_by_user(username)
    if not req:
        bot.reply(event, "\x02Error\x02: There is no request with that username")
        return
    req = req[-1]
    net = bot.manager.networkdb.get_net_by_server(req["server"]) or {"name": "Unknown"}
    reply = []
    reply.append("Request for \x02{0}\x02 to \x02{1}\x02 [\x02{2}\x02]".format(
        req["username"], req["server"], net["name"]))
    if req["status"] == "unverified":
        reply.append("is currently \x02UNVERIFIED\x02. Please check your email to "
            "verify this request")
    elif req["status"] == "pending":
        reply.append("is currently \x02PENDING\x02. Please wait for a staff member "
            "to process this request")
    elif req["status"] == "accepted":
        reply.append("was \x02\x033ACCEPTED\x0f by \x02{0}\x02. Please check your "
            "email for account details and further instructions".format(req["decided_by"]))
    elif req["status"] == "rejected":
        reply.append("was \x02\x034REJECTED\x0f. \x02Reason\x02: \x02{0}\x02".format(req["reason"]))
    bot.reply(event, " ".join(reply))

@utils.add_cmd
def emailreq(bot, event, args):
    bot.reply(event, "You may request by sending an email to requests@superbnc.com "
        "including your desired username and IRC network/server.")
    bot.reply(event, "\x02Please note\x02: the email address may not be checked often")
