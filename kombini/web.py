import glob
import os.path
import random
import time
import traceback
import urllib.request
import urllib.error
import http.cookiejar
import sqlite3
from io import StringIO

import outils.logger

MAXTRIES = 5


def retrieve_url(url, maxtries=MAXTRIES, logger=None):
    logger = outils.logger.default_logger(logger)
    tries = 0
    while True:
        try:
            return urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            if tries == 0:
                logger.debug("Failed to reach URL %s" % url)
            logger.warning("[%s]:%s" % (e.code, e.reason))
            if e.code == 404:  # not found
                logger.warning("Data not found")
                return None
            tries += 1
            if tries > maxtries:
                logger.debug(traceback.format_exc())
                logger.warning("Could not load url -> giving up")
                return None
            mt = max(10, tries * 5)
            tt = random.randrange(mt, mt + 30)
            logger.debug(traceback.format_exc())
            logger.debug("Could not load url (#%d, waiting %ds)" % (tries, tt))
            time.sleep(tt)
            continue
        except:
            raise  # unknown error
    return None


def get_firefox_cookie_jar(profile_path=None):
    if not profile_path:
        pp = glob.glob(os.path.expanduser("~/.mozilla/firefox/*.default"))
        if len(pp) != 1:
            logger = outils.logger.default_logger()
            logger.warning("More than one profile found! Aborting")
            return None
        profile_path = pp[0]
    return get_cookie_jar(os.path.join(profile_path, "cookies.sqlite"))


def get_cookie_jar(filename):
    """
    Protocol implementation for handling gsocmentors.com transactions
    Author: Noah Fontes nfontes AT cynigram DOT com
    License: MIT
    Original: http://blog.mithis.net/archives/python/90-firefox3-cookies-in-python

    Ported to Python 3 by Dotan Cohen
    """

    con = sqlite3.connect("file:%s?mode=ro" % filename, uri=True)
    # con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute("SELECT host, path, isSecure, expiry, name, value FROM moz_cookies")

    ftstr = ["FALSE", "TRUE"]

    s = StringIO()
    s.write(
        """\
# Netscape HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.
"""
    )

    for item in cur.fetchall():
        s.write(
            "%s\t%s\t%s\t%s\t%s\t%s\t%s\n"
            % (
                item[0],
                ftstr[item[0].startswith(".")],
                item[1],
                ftstr[item[2]],
                item[3],
                item[4],
                item[5],
            )
        )

    s.seek(0)
    cookie_jar = http.cookiejar.MozillaCookieJar()
    cookie_jar._really_load(s, "", True, True)

    return cookie_jar
