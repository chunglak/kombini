import os


def home_tilde(fn: str) -> str:
    """
    Replace the HOME part in filename by tilde
    """
    h = os.getenv("HOME")
    if not h:
        return fn
    if fn.startswith(h):
        return "~" + fn[len(h) :]
    else:
        return fn
