import hashlib
import operator
import os
import platform
import sys

def open_file(fn):

    pf = platform.system()
    if pf == "Linux":
        os.system("xdg-open %s" % fn)
    elif pf == "Darwin":
        os.system("open %s" % fn)
    else:
        raise

def recurse_paths(path, followlinks=False):
    """
    Create a list of all the files in a path (recursive, full paths)
    """
    for root, _, files in os.walk(path, followlinks=followlinks):
        for fn in files:
            yield os.path.join(root, fn)

def get_lines(fn=None, split=True, strip=False):
    if fn and os.path.isfile(fn):
        lines = open(fn, "r").read()
    else:
        lines = sys.stdin.read()
    if split:
        lines = lines.split("\n")
    if strip:
        lines = list(filter(None, map(operator.methodcaller("strip"), lines)))
    return lines

def directory_size(pth, followlinks=False):
    n = 0
    for root, _, files in os.walk(pth, followlinks=followlinks):
        for fn in files:
            n += os.path.getsize(os.path.join(root, fn))
    return n


def hash_file(fn):
    """
    Unique identifier for a file
    """
    BLOCKSIZE=2**26 #64MB
    m=hashlib.sha3_256()
    with open(fn,'rb') as fh:
        buf=fh.read(BLOCKSIZE)
        while len(buf)>0:
            m.update(buf)
            buf=fh.read(BLOCKSIZE)
    return m.hexdigest()
