import sys


def on_android_p():
    return hasattr(sys, "getandroidapilevel")
