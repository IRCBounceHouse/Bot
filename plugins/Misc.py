import utils

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
