import collections
import json
import os, os.path
import pprint
import re
import time
import urllib.parse
import webbrowser

import requests

import outils.logger
import outils.input

logger = outils.logger.default_logger()

SPOTIFY_AUTHORIZATION_URL = "https://accounts.spotify.com/authorize"
TOKEN_EXCHANGE_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com"
SCOPES = [
    "playlist-modify-private",
    "playlist-modify-public",
    "playlist-read-private",
    "user-library-modify",
    "user-library-read",
    "user-read-currently-playing",
    "user-read-recently-played",
]

SPOTIFY_DIR = os.path.expanduser("~/var/tify")
if not os.path.isdir(SPOTIFY_DIR):
    os.makedirs(SPOTIFY_DIR)
CODE_FN = os.path.join(SPOTIFY_DIR, "auth_code")
ACCESS_TOKEN_FN = os.path.join(SPOTIFY_DIR, "access_token")
REFRESH_TOKEN_FN = os.path.join(SPOTIFY_DIR, "refresh_token")
APP_FN = os.path.join(SPOTIFY_DIR, "app_creds")

STATUS_OK = 200
STATUS_UNAUTHORIZED = 401
STATUS_BAD_GATEWAY = 502

Response = collections.namedtuple("Response", ["ok", "data"], defaults=[False, None])

# --------------------------------------------------
# Authentication
# --------------------------------------------------
def get_app_creds(fn=None):
    fn = fn if fn else APP_FN
    try:
        return json.load(open(fn, "r"))
    except FileNotFoundError:
        return None


def get_code(fn=None):
    fn = fn if fn else CODE_FN
    try:
        return open(fn, "r").read()
    except FileNotFoundError:
        return None


def get_access_token(fn=None):
    fn = fn if fn else ACCESS_TOKEN_FN
    try:
        return open(fn, "r").read()
    except FileNotFoundError:
        return None


def get_refresh_token(fn=None):
    fn = fn if fn else REFRESH_TOKEN_FN
    try:
        return open(fn, "r").read()
    except FileNotFoundError:
        return None


def _auth_header():
    token = get_access_token()
    return {"Authorization": "Bearer %s" % token}


def fetch_access_token():
    """
    Call this after obtaining a new authorization code
    or when old access token doesn't work anymore
    """
    C = get_app_creds()
    if C is None:
        s = "Cannot load app credentials!"
        logger.error(s)
        return Response(ok=False, data=s)

    code = get_code()
    if code:
        logger.info("Fetching from authorization code")
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": C["REDIRECT_URI"],
        }
    else:
        token = get_refresh_token()
        if not token:
            s = "No refresh token and no code!"
            logger.error(s)
            return Response(ok=False, data=s)
        logger.info("Fetching from refresh code")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token,
        }

    r = requests.post(
        TOKEN_EXCHANGE_URL, auth=(C["CLIENT_ID"], C["CLIENT_SECRET"]), data=data
    )
    if r.status_code == STATUS_OK:
        new_resp = r.json()
        open(ACCESS_TOKEN_FN, "w").write(new_resp["access_token"])
        logger.info("Token fetched")
        if code:
            logger.info("Removing code file")
            os.remove(CODE_FN)
            logger.info("Saving new refresh token")
            open(REFRESH_TOKEN_FN, "w").write(new_resp["refresh_token"])
        return Response(ok=True)
    else:
        s = "%s [%s]" % (r.reason, r.status_code)
        logger.error(s)
        return Response(ok=False, data=s)


def fetch_access_token0():
    """
    Call this after obtaining a new authorization code
    or when old access token doesn't work anymore
    """
    C = get_app_creds()
    if C is None:
        s = "Cannot load app credentials!"
        logger.error(s)
        return Response(ok=False, data=s)

    code = get_code()
    if code:
        logger.info("Fetching from authorization code")
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": C["REDIRECT_URI"],
        }
    else:
        resp = get_resp()
        if not resp:
            s = "No resp and no code!"
            logger.error(s)
            return Response(ok=False, data=s)
        logger.info("Fetching from refresh code")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": resp["refresh_token"],
        }

    r = requests.post(
        TOKEN_EXCHANGE_URL, auth=(C["CLIENT_ID"], C["CLIENT_SECRET"]), data=data
    )
    if r.status_code == STATUS_OK:
        new_resp = r.json()
        json.dump(new_resp, open(RESP_FN, "w"))
        logger.info("Token fetched")
        if code and outils.input.yes_or_no("Delete code file?"):
            os.remove(CODE_FN)
        return Response(ok=True)
    else:
        s = "%s [%s]" % (r.reason, r.status_code)
        logger.error(s)
        return Response(ok=False, data=s)


def get_authorization_code_from_user(client_id=None, redirect_uri=None, scopes=None):
    """
    Paste url returned by this function in a browser
    Follow intructions in browser
    A url is returned with a "code=..." part
    Put this part (without code=) in a file at CODE_FN
    """
    C = get_app_creds()
    if C is None:
        s = "Cannot load app credentials!"
        logger.error(s)
        return None

    params = {
        "client_id": client_id if client_id else C["CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": redirect_uri if redirect_uri else C["REDIRECT_URI"],
        "scope": " ".join(scopes if scopes else SCOPES),
    }
    url = "%s?%s" % (SPOTIFY_AUTHORIZATION_URL, urllib.parse.urlencode(params))
    return url


# --------------------------------------------------
# API Calls
# --------------------------------------------------
def api_search(q, type_=None):
    if not type_:
        type_ = "track"
    params = {"q": q, "type": type_}
    r = requests.get(
        "%s/v1/search" % API_BASE_URL, headers=_auth_header(), params=params
    )
    if r.status_code == STATUS_OK:
        return Response(ok=True, data=r.json())
    else:
        return Response(ok=False, data=r)


# --------------------------------------------------
#
# --------------------------------------------------
def add_songs_to_playlist(plid, song_uris):
    headers = _auth_header()
    headers["Content-Type"] = "application/json"
    body = {"uris": song_uris}
    r = requests.post(
        "%s/v1/playlists/%s/tracks" % (API_BASE_URL, plid),
        headers=headers,
        data=json.dumps(body),
    )
    if r.status_code == 201:
        return Response(ok=True, data=None)
    else:
        return Response(ok=False, data=r)


def get_playlists():
    playlists = []
    r = requests.get("%s/v1/me/playlists" % API_BASE_URL, headers=_auth_header())
    while True:
        if r.status_code == STATUS_OK:
            data = r.json()
            playlists.extend(data["items"])
            if data["next"]:
                r = requests.get(data["next"], headers=_auth_header())
            else:
                return Response(ok=True, data=playlists)
        else:
            return Response(ok=False, data=r)


# --------------------------------------------------
#
# --------------------------------------------------
def find_song(title=None, artist=None, album=None, override=None, process=False):
    def transform_artist(s):
        s = unidecode.unidecode(s.lower())
        s = s.replace("the ", "")
        s = s.replace(",", " ")
        s = s.replace("'", "")
        s = s.replace(" & ", "; ")
        s = s.replace(" and ", "; ")
        return s

    def transform_title(s):
        s = unidecode.unidecode(s.lower())

        m = re.match(r"(.+)\(.+\)(.*)", s)
        if m:
            g1, g2 = m.groups()
            s = "%s %s" % (g1.strip(), g2.strip())

        m = re.match(r"(.+)\[.+\](.*)", s)
        if m:
            g1, g2 = m.groups()
            s = "%s %s" % (g1.strip(), g2.strip())

        m = re.match(r"(.+)-(.*)remaster(.*)", s)
        if m:
            s = m.groups()[0].strip()

        s = s.replace("the ", "")
        s = s.replace("'", "")
        s = s.replace(" & ", " and ")
        return s

    def process_item(item):
        # iartist=item['artists'][0]['name']
        iartist = "; ".join([rec["name"] for rec in item["artists"]])
        ialbum = item["album"]["name"]
        ititle = item["name"]
        popularity = item["popularity"]
        ta1, ta2 = transform_artist(artist), transform_artist(iartist)
        tt1, tt2 = transform_title(title), transform_title(ititle)
        pdata = {
            "artist": iartist,
            "album": ialbum,
            "ititle": ititle,
            "popularity": popularity,
            "score": fuzz.ratio(ta1, ta2),
            "score2": fuzz.partial_ratio(ta1, ta2),
            "score_v": (ta1, ta2),
            "score_title": fuzz.ratio(ta1, ta2),
            "score_title2": fuzz.partial_ratio(ta1, ta2),
            "score_title_v": (tt1, tt2),
        }
        return {
            "pdata": pdata,
            "raw": item,
        }

    def keysort(p):
        P = p["pdata"]
        return (
            max(P["score"], P["score2"]),
            max(P["score_title"], P["score_title2"]),
            P["popularity"],
        )

    from fuzzywuzzy import fuzz #type:ignore
    import unidecode #type:ignore

    if override:
        q = override
    else:
        qartist = ("artist:%s" % transform_artist(artist)) if artist else ""
        qtitle = ("track:%s" % transform_title(title)) if title else ""
        qalbum = ("album:%s" % album) if album else ""
        q = " ".join([qartist, qtitle, qalbum])
    params = {"q": q, "type": "track", "limit": 50, "market": "JP"}
    r = requests.get(
        "%s/v1/search" % API_BASE_URL, headers=_auth_header(), params=params
    )
    if r.status_code == STATUS_OK:
        data = r.json()
        if process:
            ps = list(map(process_item, data["tracks"]["items"]))
            data = sorted(ps, key=lambda p: keysort(p), reverse=True)
        return Response(ok=True, data=data)
    else:
        return Response(ok=False, data=r)
