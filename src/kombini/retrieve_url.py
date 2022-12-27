from __future__ import annotations  # PEP 585

import logging
import random
import time
import traceback
import urllib.request
import urllib.response

MAXTRIES = 5


def retrieve_url(
    url: str, maxtries: int = MAXTRIES
) -> urllib.response.addinfourl | None:
    tries = 0
    while True:
        try:
            return urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            if tries == 0:
                logging.debug("Failed to reach URL %s" % url)
            logging.warning("[%s]:%s" % (e.code, e.reason))
            if e.code == 404:  # not found
                logging.warning("Data not found")
                return None
            tries += 1
            if tries > maxtries:
                logging.debug(traceback.format_exc())
                logging.warning("Could not load url -> giving up")
                return None
            mt = max(10, tries * 5)
            tt = random.randrange(mt, mt + 30)
            logging.debug(traceback.format_exc())
            logging.debug("Could not load url (#%d, waiting %ds)" % (tries, tt))
            time.sleep(tt)
            continue
        except:
            raise  # unknown error
    return None
