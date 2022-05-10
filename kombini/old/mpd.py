# ==============================================================================
# Imports
# ==============================================================================
# -System-----------------------------------------------------------------------
import gzip
import os
import os.path
import pickle
import re
import socket
import subprocess
import typing as ty

# -Third party------------------------------------------------------------------
# -Own modules------------------------------------------------------------------
# import outils.logger
from outils.logger import default_logger

# ==============================================================================
# Constants
# ==============================================================================
MPD_ROOT = os.path.expanduser("~/.config/mpd")
MPD_PLAYLISTS = os.path.join(MPD_ROOT, "playlists")
MPD_MUSIC = os.path.join(MPD_ROOT, "music")

# only 'file' key
DB_PICKLE = os.path.expanduser("~/var/mpd.pickle.gz")
# whole mpd database
MPDDB_PICKLE = os.path.expanduser("~/var/mpddb.pickle.gz")

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6600

logger = default_logger()

# ------------------------------------------------------------
#
# ------------------------------------------------------------
class MPDInterface:
    def __init__(
        self,
        host=None,
        port=None,
        mpd_playlists=None,
        mpd_music=None,
        db_pickle=None,
        refresh_db=False,
        logger=None,
    ):
        self.logger = default_logger(logger)
        self.host=host
        self.port=port
        self.mpd_playlists = mpd_playlists if mpd_playlists else MPD_PLAYLISTS
        self.mpd_music = mpd_music if mpd_music else MPD_MUSIC
        self.db_pickle = db_pickle if db_pickle else MPDDB_PICKLE
        self.refresh_db = refresh_db
        self._db=None

    # --------------------------------------------------------------------------
    #
    # --------------------------------------------------------------------------
    def playlist_path(self, pl):
        return os.path.join(self.mpd_playlists, "%s.m3u" % pl)

    def song_path(self, s):
        return os.path.join(self.mpd_music, s)

    @property
    def mpddb(self):
        if self._db is None:
            self._db = load_mpddb(
                db_pickle=self.db_pickle,
                host=self.host,
                port=self.port,
                refresh=self.refresh_db,
            )
        return self._db

    @property
    def songdb(self):
        return self.mpddb["file"]

    @property
    def all_songs(self):
        return list(self.songdb)

    @property
    def playlists(self):
        ps = self.mpddb["playlist"]
        return [p for p in ps if "/" not in p]

    def playlist_contents(self, pl: str) -> ty.Optional[ty.List[str]]:
        try:
            return loadlines(self.playlist_path(pl))
        except FileNotFoundError:
            self.logger.warning("No such playlist: %s" % pl)
            return None

    def save_playlist(self, pl: str, ss: ty.List[str]):
        open(self.playlist_path(pl), "w").write("\n".join(ss) + "\n")
        self.logger.info("Wrote playlist %s (%d songs)" % (pl, len(ss)))


# ------------------------------------------------------------
# Direct interaction with server
# ------------------------------------------------------------
def query_server(cmd, host=None, port=None, split_it=False):
    host = host if host else DEFAULT_HOST
    port = port if port else DEFAULT_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    sock.connect(server_address)
    data = sock.recv(1024)
    if data[:2] != b"OK":
        raise
    cmd += "\n"
    sock.sendall(cmd.encode("utf-8"))
    data = b""
    while True:
        chunk = sock.recv(2 ** 16)
        data += chunk
        if chunk.endswith(b"OK\n"):
            data = data[:-3]
            break
    r = data.decode("utf-8")
    if split_it:
        return list(filter(None, [l.strip() for l in r.split("\n")]))
    else:
        return r


def fetch_mpddb(host=None, port=None):
    return query_server("listallinfo", host=host, port=port, split_it=True)


def parse_mpddb(lines):
    """
    Format is "key: value"
    If key is one of file, directory or playlist, the following lines
       refer to that object
    """
    rez = {"file": {}, "directory": {}, "playlist": {}}
    cur, curtype = None, None
    for line in lines:
        if not line:
            continue
        m = re.match("(.+?): (.+)", line)
        if not m:
            continue
        k, v = m.groups()
        if k in rez:
            if curtype:
                rez[curtype][cur[curtype]] = cur
            cur, curtype = {k: v}, k
        else:
            cur[k] = v
    rez[curtype][cur[curtype]] = cur
    return rez


def fetch_whole_database(host=None, port=None):
    return parse_mpddb(fetch_mpddb(host=host, port=port))
    # ls = query_server("listallinfo", host=host, port=port, split_it=True)
    # rez = {"file": {}, "directory": {}, "playlist": {}}
    # cur, curtype = None, None
    # for l in ls:
    #     if not l:
    #         continue
    #     m = re.match("(.+?): (.+)", l)
    #     k, v = m.groups()
    #     # v=conv(v)
    #     if k in rez:
    #         if curtype:
    #             rez[curtype][cur[curtype]] = cur
    #         cur, curtype = {k: v}, k
    #     else:
    #         cur[k] = v
    # return rez


# ------------------------------------------------------------
# Interaction through mpc
# ------------------------------------------------------------
def mpcmd(*parms):
    cmd = ["mpc"] + list(parms)
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return r.stdout.decode("utf-8")


# ------------------------------------------------------------
#
# ------------------------------------------------------------
def loadlines(f):
    return [s for s in [l.strip() for l in open(f, "r")] if s]

def load_mpddb(db_pickle=None, host=None, port=None, refresh=False):
    if not db_pickle:
        db_pickle = MPDDB_PICKLE
    if os.path.isfile(db_pickle) and not refresh:
        logger.info("Loading songdb from %s" % db_pickle)
        _db = pickle.load(gzip.open(db_pickle, "rb"))
    else:
        logger.info("Fetching songdb from server")
        _db = fetch_whole_database(host=host, port=port)
        logger.info("Saving songdb to %s" % db_pickle)
        pickle.dump(_db, gzip.open(db_pickle, "wb"))
    return _db


# ------------------------------------------------------------
# LEGACY
# ------------------------------------------------------------
def fetch_song_metadata(path, host=None, port=None):
    def spl(s):
        n = s.find(":")
        if n == -1:
            return None
        return s[:n], s[n + 2 :]

    r = query_server('find file "%s"' % path, host=host, port=port, split_it=True)
    if not r:
        return None
    rez = dict([x for x in map(spl, r) if x])
    if "Time" in rez:
        rez["Time"] = int(rez["Time"])
    if "duration" in rez:
        rez["duration"] = float(rez["duration"])
    # if 'Last-Modified' in rez: rez['Last-Modified']=float(rez['Last-Modified'])
    return rez
