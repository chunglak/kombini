import time

import outils.string as OuS

def item_counter(t0, i, n=None):
    if not i:
        return ""
    te = time.time() - t0
    tps = te / i
    if n:
        return "%d/%d (%d%%|%.1fms|%s left|%s elapsed)" % (
            i,
            n,
            i / n * 100,
            tps * 1000,
            OuS.duration_string((n - i) * tps),
            OuS.duration_string(te),
        )
    else:
        return "%d (%.1fms|%s elapsed)" % (
            i,
            tps * 1000,
            OuS.duration_string(te),
        )

def parse_datetime(s):
    from dateutil.parser import parse
    import pytz

    tzinfos = {tz: pytz.timezone(tz) for tz in pytz.all_timezones}
    return parse(s, tzinfos=tzinfos)
