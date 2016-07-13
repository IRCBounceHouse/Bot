import utils

@utils.add_cmd
def servers(bot, event, args):
    bot.reply(event, ", ".join(["\x02{0}\x02: {1}".format(s.name,
        "\x02\x033UP\x0f" if s.connected else "\x02\x034DOWN\x0f")
        for s in sorted(bot.manager.connections["znc"].values(),
        key=lambda v: v.name)]))

@utils.add_cmd
def clients(bot, event, args):
    try:
        client = args.split()[0]
        if client.lower() == "atomic":
            bot.reply(event, "Please see http://wiki.znc.in/Atomic")
        elif client.lower() == "hexchat" or client.lower() == "xchat":
            bot.reply(event, "Please see http://wiki.znc.in/HexChat")
        elif client.lower() == "irssi":
            bot.reply(event, "Please see http://wiki.znc.in/Irssi")
        elif client.lower() == "mirc":
            bot.reply(event, "Please see http://wiki.znc.in/MIRC")
        elif client.lower() == "pidgin":
            bot.reply(event, "We recommend using a different client since Pidgin "
                "isn't a very good IRC client. If you still wish to use Pidgin, "
                "please see http://wiki.znc.in/Pidgin and pay special attention "
                "to http://wiki.znc.in/Pidgin#Channels")
        elif client.lower() == "weechat":
            bot.reply(event, "Please see http://wiki.znc.in/WeeChat")
        else:
            bot.reply(event, "Please see http://wiki.znc.in/Connecting_to_ZNC and "
                "http://wiki.znc.in/Category:Clients")
    except IndexError:
        bot.reply(event, "Please see http://wiki.znc.in/Connecting_to_ZNC and "
            "http://wiki.znc.in/Category:Clients")

@utils.add_cmd
def ports(bot, event, args):
    bot.reply(event, "\x02SSL\x02: 5000, 6697 \x02Non-SSL\x02: 6667")
