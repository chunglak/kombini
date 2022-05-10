import json
import os
import time
import subprocess

import outils.time as OuT

def get_music_files(path):
    """
    Given a path, return a list of all the audio files in that path
    """
    fs = [
        os.path.join(root, f) for root, dirs, files in os.walk(path) for f in files
    ]
    rez = {}
    t0 = time.time()
    n = len(fs)
    for i, f in enumerate(fs):
        md = get_ffprobe_info(f)
        print(" " + OuT.item_counter(t0, i + 1, n) + "   ", end="\r")
        # print(' '+item_counter(t0,i+1,n)+'   ',end='\r')
        if not md:
            print("Could not get info on %s" % f)
            continue
        ss = md["streams"]
        ok = False
        for s in ss:
            if s["codec_type"] == "audio":
                rez[f] = md
                rez[f]["audio_stream"] = s
                ok = True
                break
        if not ok:
            print("No audio in %s" % f)
    print()
    return rez

def get_ffprobe_info(fn, verbose=True):
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
            print(rez)
        return None
    return json.loads(rez.stdout.decode("utf-8"))
