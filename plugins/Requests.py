import socket
import re

import utils

@utils.add_cmd
def request(bot, event, args):
    if event.target.startswith("#"):
        bot.reply(event, "You cannot request an account in the public channel because we require your email address. Instead, Private Message botface.")
        return
    if len(args.split(" ")) < 2:
        bot.reply(event, "\x02Syntax\x02: !request <username> <email>")
        bot.reply(event, "\x02Terms of Service\x02: https://ircbouncehouse.com/info")
        return
    args = args.split(" ")
    username = args[0]
    if not re.fullmatch("^[a-zA-Z][a-zA-Z@._\-]+$", username):
        bot.reply(event, "\x02Error\x02: Invalid username.")
        return
    email = args[1]
    if "@" not in email:
        bot.reply(event, "\x02Error\x02: Invalid email specified.")
        return
    requsers = bot.manager.requestdb.get_by_user(username)
    if requsers:
        for requser in requsers:
            if requser["status"] != "rejected":
                bot.reply(event, "\x02Error\x02: There is already a request with this username.")
                return
    reqemails = bot.manager.requestdb.get_by_email(email)
    if reqemails:
        for reqemail in reqemails:
            if reqemail["status"] != "rejected":
                bot.reply(event, "\x02Error\x02: There is already a request with this email.")
                return
    bot.manager.requestdb.add(username, email, str(event.source))
    thisreq = bot.manager.requestdb.get_by_email(email)[-1]
    key = utils.genkey()
    bot.manager.verifydb.add(key, "request", thisreq["id"])
    bot.manager.mail.verify(email, key)
    bot.reply(event, "\x02You have completed the first step!\x02 Please follow the instructions sent to the email address you specified to verify your request.")

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
        bot.reply(event, "\x02Your email has now been verified!\x02 Please wait for a staff member to process your request. You can check the status of your request by using \x02!check {0}\x02".format(req["username"]))
        reqdata = []
        reqdata.append("\x02ID\x02: {0}".format(req["id"]))
        reqdata.append("\x02Username\x02: {0}".format(req["username"]))
        reqdata.append("\x02Email\x02: {0}".format(req["email"]))
        reqdata.append("\x02Source\x02: {0}".format(req["source"]))
        bot.msg("#IRCBounceHouse-dev", "\x02NEW REQUEST\x02: {0}".format(", ".join(reqdata)))
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
    reply = []
    reply.append("Request for \x02{0}\x02".format(req["username"]))
    if req["status"] == "unverified":
        reply.append("is currently \x02UNVERIFIED\x02. Please check your email to verify this request.")
    elif req["status"] == "pending":
        reply.append("is currently \x02PENDING\x02. Please wait for a staff member to process this request.")
    elif req["status"] == "accepted":
        reply.append("was \x02\x033ACCEPTED\x0f. Please check your email for account details and further instructions.")
    elif req["status"] == "rejected":
        reply.append("was \x02\x034REJECTED\x0f. \x02Reason\x02: {0}".format(req["reason"]))
    bot.reply(event, " ".join(reply))
