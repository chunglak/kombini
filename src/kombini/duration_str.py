from __future__ import annotations  # PEP 585


def duration_str(ns: int | float) -> str:
    """
    Return a human-readable representation of
    a duration in seconds
    """
    s = ""
    if ns >= 3600:
        h = int(ns / 3600)
        s += f"{h}h"
        ns -= 3600 * h
    if ns >= 60:
        m = int(ns / 60)
        s += f"{m}m"
        ns -= m * 60
    if ns:
        s += f"{int(ns)}s"
    return s
