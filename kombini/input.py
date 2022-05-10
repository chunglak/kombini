import datetime

def input_choice(msg, choices):
    while True:
        r = input(msg)
        if not r:
            continue
        if r not in choices:
            continue
        return r

def yes_or_no(msg):
    """
    ::string->IO bool
    """
    while 1:
        r = input(msg)
        if not r:
            continue
        if r.lower()[0] == "y":
            return True
        elif r.lower()[0] == "n":
            return False
        else:
            print("Please answer by y[es] or n[o]")

def conv(v):
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if v.lower() == "none":
        return None
    try:
        return datetime.datetime.strptime(v, "%Y-%m-%d").date()
    except ValueError:
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except ValueError:
                return v
