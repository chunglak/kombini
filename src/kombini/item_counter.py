def item_counter(t0: float, i: int, n: int | None = None) -> str:
    def duration_string(s):
        ds = duration_string
        if s < 60:
            return "%ds" % s
        elif s < 60 * 60:
            m = int(s / 60)
            return "%dm%s" % (m, ds(s - m * 60))
        elif s < 24 * 3600:
            h = int(s / 3600)
            return "%dh%s" % (h, ds(s - h * 3600))
        elif s < 365.25 * 86400:
            d = int(s / 86400)
            return "%dd%s" % (d, ds(s - d * 86400))
        else:
            y = int(s / (365.25 * 86400))
            return "%dy%s" % (y, ds(s - y * 365.25 * 86400))

    import time  # pylint:disable=import-outside-toplevel

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
            duration_string((n - i) * tps),
            duration_string(te),
        )
    else:
        return "%d (%.1fms|%s elapsed)" % (
            i,
            tps * 1000,
            duration_string(te),
        )
