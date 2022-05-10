from __future__ import annotations  # PEP 585

import json
import logging
import subprocess


def get_ffprobe_info(fn: str, verbose=True) -> dict | None:
    """
    Use ffprobe to extract information about a media file
    Returns a dictionary, with 2 keys:
        - format (metadata)
        - streams (info about streams)
    """
    cmd = "ffprobe -show_format -show_streams -v quiet -print_format json -i"
    args = cmd.split(" ") + [fn]
    rez = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if rez.returncode != 0:
        if verbose:
            logging.error(str(rez))
        return None
    return json.loads(rez.stdout.decode("utf-8"))
