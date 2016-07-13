import utils

@utils.add_cmd
def request(bot, event, args):
    bot.reply(event, "The request feature is not yet implemented. If you would "
        "like to request an account, just ask one of the staff (we're opped) or "
        "see !emailreq for details on requesting an account by email.")

@utils.add_cmd
def emailreq(bot, event, args):
    bot.reply(event, "You may request by sending an email to requests@superbnc.com "
        "including your desired username and IRC network/server.")
