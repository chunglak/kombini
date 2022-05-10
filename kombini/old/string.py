import locale
from math import sqrt

import outils.terminal as OuTe


def _fmt_num(n, t, b, m, k):
    def fint(x):
        if x == int(int(x * 10) / 10):
            return "{:,}".format(x)
        else:
            return "{:,.1f}".format(x)

    if n >= 1e12:
        return fint(n / 1e12) + t
    elif n >= 1e9:
        return fint(n / 1e9) + b
    elif n >= 1e6:
        return fint(n / 1e6) + m
    elif n >= 1000:
        return fint(n / 1000) + k
    else:
        return int(n)


def decorate(msg, len_=0, ln=True):
    """
    Surround msg with lines of "="
        use len_ to specify a length of '=' > length of msg
    """
    l = max(len_, len(msg))
    return "=" * l + "\n" + msg.center(len_) + "\n" + "=" * l + ("\n" if ln else "")


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


def fmt_num(n):
    return _fmt_num(n, "t", "b", "m", "k")


def fmt_num_bytes(n):
    return _fmt_num(n, "TB", "GB", "MB", "KB")


def numf(n):
    """
    Return integer n with 000s separated by commas
    """
    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    except: #pylint:disable=bare-except
        locale.setlocale(locale.LC_ALL, "usa")
    try:
        return locale.format("%d", int(n), grouping=True)
    except ValueError:
        return n


def format_table(
    data,
    width=None,
    just="l",
    left_space=1,
    right_space=1,
    escape_ansi=False,
    vert_sep=False,
):
    """
    Return a list of strings formatting data contained in "data" in columns
    """

    def cut_string(s, tl):
        r = 0
        rr = []
        while r < len(s):
            rr.append(s[r : r + tl])
            r += tl
        # print '\n'.join(rr)
        return "\n".join(rr)

    def pad(word, width, just=just):
        word = str(word)
        l = len(word) if not escape_ansi else OuTe.raw_len(word)
        ll = max(0, width - l)
        if just == "l":
            rez = word + (" " * ll)
        elif just == "r":
            rez = (" " * ll) + word
        elif just == "c":
            hl = int(ll / 2)
            rez = (" " * hl) + word + (" " * (ll - hl))
        else:
            rez = word + (" " * ll)
        return (" " * left_space) + rez + (" " * right_space)

    rez = []

    if not data:
        return ""

    if width:
        wt = [width for i in range(max([len(row) for row in data]))]
    else:
        # find smallest size for each column
        wt = [0 for i in range(max([len(row) for row in data if not isinstance(row,str)]))]
        nw = len(wt)
        for row in data:
            if type(row) is str:
                continue
            for j, el in enumerate(row):
                if (type(el) == list) or (type(el) == tuple):
                    elm = el[0]
                else:
                    elm = el
                if escape_ansi:
                    l = OuTe.raw_len(str(elm))
                else:
                    l = len(str(elm))
                if l > wt[j]:
                    wt[j] = l
        wt = [x for x in wt]

    tot_len = sum(wt) + len(wt) * (left_space + right_space)
    if vert_sep:
        tot_len += nw - 1

    for row in data:
        if row == "sep":
            rez.append("-" * tot_len)
            continue
        elif row[:2] == "@@":
            rez.append(cut_string(row[2:], tot_len))
            continue
        row2 = ""
        for j, cell in enumerate(row):
            if vert_sep and j:
                row2 += "|"
            if (type(cell) == list) or (type(cell) == tuple):
                row2 += pad(cell[0], wt[j], cell[1])
            else:
                if cell == "&&sep":
                    rez.append("-" * tot_len)
                else:
                    row2 += pad(cell, wt[j])
        rez.append(row2)

    return "\n".join(rez)


def text_histogram(
    data,
    nb_buckets=10,
    min_bucket=None,
    max_bucket=None,
    print_it=True,
    width=60,
    delete_empty_buckets=False,
    buck_fmt="%d",
    stat_fmt="%.2f",
    bar_char="*",
):
    """
    Create a text histogram (vertical)
        data    dict value->qty
    """
    try:
        if len(data) == 0 or sum(data.values()) == 0:
            return None
        if min_bucket != None:
            min_ = min_bucket
        else:
            min_ = min(data)
        if max_bucket != None:
            max_ = max_bucket
        else:
            max_ = max(data)
        dx = (max_ - min_) / nb_buckets
        buckets = [0] * nb_buckets
        for v in data:
            n = int((v - min_) / dx)
            if n >= len(buckets):
                n = len(buckets) - 1
            buckets[n] += data[v]

        n = sum(data.values())
        avg = sum([k * data[k] for k in data]) / n
        std = sqrt(sum([data[k] * ((k - avg) ** 2) for k in data]) / n)

        # calculate median
        v = list(data.keys())
        v.sort()
        # WHAT IS THIS LINE FOR?
        # dd=min([(v[i+1]-v[i]) for i in range(len(v)-1)])
        c = 0
        x = 0
        while c < (n / 2):
            c += data[v[x]]
            x += 1
        med = v[x - 1]

        if not print_it:
            return {
                "buckets": buckets,
                "min": min_,
                "max": max_,
                "dx": dx,
                "avg": avg,
                "std": std,
                "med": med,
            }

        rez = []
        mb = max(buckets)
        if mb == 0:
            return None
        ratio = width / mb
        tot = sum(buckets)
        for i, b in enumerate(buckets):
            if b or (not delete_empty_buckets):
                e1 = (buck_fmt % (min_ + i * dx), "r")
                e2 = (buck_fmt % (min_ + (i + 1) * dx), "r")
                if b:
                    e3 = (numf(b), "r")
                    e4 = ("%d%%" % (b / tot * 100), "r")
                else:
                    e3 = e4 = ""
                e5 = (bar_char * int(b * ratio), "l")
                rez.append([e1, e2, e3, e4, e5])
        rez = format_table(rez)
        rez += "\n\nAvg=%s Std=%s Med=%s #=%d" % (
            stat_fmt % avg,
            stat_fmt % std,
            stat_fmt % med,
            tot,
        )
        return rez
    except Exception as e:
        print(e)
        return None
