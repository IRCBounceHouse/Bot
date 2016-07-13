import collections

events = []

def add_cmd(func=None, **kwargs):
    def wrapper(func):
        func._event = "command"
        func._cmdname = kwargs.get("command", func.__name__)
        func._prefix = kwargs.get("prefix", "!")
        func._perms = kwargs.get("perms", "all")
        events.append(func)
    if isinstance(func, collections.Callable):
        return wrapper(func)
    return wrapper

def add_trigger(func=None, **kwargs):
    def wrapper(func):
        func._event = "trigger"
        func._trigger = kwargs.get("trigger", "ALL")
        events.append(func)
    if isinstance(func, collections.Callable):
        return wrapper(func)
    return wrapper
