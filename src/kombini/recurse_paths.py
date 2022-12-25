from __future__ import annotations  # PEP 585

import os, os.path
import typing


def recurse_paths(path: str, followlinks: bool = False) -> typing.Iterator:
    """
    Return an iterator on all the file in tree
    """
    for root, _, files in os.walk(path, followlinks=followlinks):
        for fn in files:
            yield os.path.join(root, fn)
