import utils

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
            bot.reply(event, "We recommend using a different client since Pidgin isn't a very good IRC client. If you still wish to use Pidgin, please see http://wiki.znc.in/Pidgin and pay special attention to http://wiki.znc.in/Pidgin#Channels")
        elif client.lower() == "weechat":
            bot.reply(event, "Please see http://wiki.znc.in/WeeChat")
        else:
            bot.reply(event, "Please see http://wiki.znc.in/Connecting_to_ZNC and http://wiki.znc.in/Category:Clients")
    except IndexError:
        bot.reply(event, "Please see http://wiki.znc.in/Connecting_to_ZNC and http://wiki.znc.in/Category:Clients")

@utils.add_cmd
def ports(bot, event, args):
    bot.reply(event, "\x02IRC SSL\x02: 6697 \x02IRC Non-SSL\x02: 6667 \x02Web-Admin\x02: 8080")

@utils.add_cmd
def ping(bot, event, args):
    bot.reply(event, "pong")

@utils.add_cmd(command="list")
def cmdlist(bot, event, args):
    commands = {}
    for plugin in bot.manager.plugins:
        commands[plugin.replace("plugins.", "", 1)] = [c._cmdname for c in
            bot.manager.events if c._event == "command" and c.__module__ == plugin
            and (bot.hasperm(c._perms, event.source) or c._perms == "all")]
    bot.reply(event, " ".join(["\x02{0}\x02: {1}".format(p, ", ".join([
        cmd for cmd in sorted(c) ])) for p, c in sorted(commands.items(),
        key=lambda v: v[0]) if len(c) > 0]))
