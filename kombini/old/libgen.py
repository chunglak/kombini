# ==============================================================================
# Imports
# ==============================================================================
# -System-----------------------------------------------------------------------
import csv
import os, os.path
import time

# -Third party------------------------------------------------------------------
# -Own modules------------------------------------------------------------------
import outils.logger
import outils.string
import outils.time

logger = outils.logger.default_logger()

# ==============================================================================
# Constants
# ==============================================================================
LIBGEN_DIR = os.path.expanduser("~/work/libgen")
LIBGEN_CSV_FILE = os.path.join(LIBGEN_DIR, "libgen_content.csv")
# LIBGEN_CSV_FILE = os.path.join(LIBGEN_DIR, "libgen_content.short.csv")
LIBGEN_ERR_FILE = os.path.join(LIBGEN_DIR, "libgen_content.errors.txt")
LIBGEN_REZ_FILE = os.path.join(LIBGEN_DIR, "libgen_content.fzf")

LIBGEN_CSV_FIELDS = [
    "id",
    "title",
    "volumeinfo",
    "series",
    "periodical",
    "author",
    "year",
    "edition",
    "publisher",
    "city",
    "pages",
    "pages2",
    "language",
    "topic",
    "library",
    "issue",
    "identifier",
    "issn",
    "asin",
    "udc",
    "lbc",
    "ddc",
    "lcc",
    "doi",
    "googlebookid",
    "openLibraryid",
    "commentary",
    "dpi",
    "color",
    "cleaned",
    "orientation",
    "paginated",
    "scanned",
    "bookmarked",
    "searchable",
    "filesize",
    "extension",
    "md5",
    "generic",
    "visible",
    "locator",
    "local",
    "timeadded",
    "timelastmodified",
    "coverurl",
    "identifierwodash",
    "tags",
    "pagesinfile",
]


def parsetime(s):
    from dateutil.parser import parse

    return parse(s).date()


LIBGEN_FIELDS_PARSERS = {
    "timeadded": (parsetime, "INTEGER"),
    "timelastmodified": (parsetime, "INTEGER"),
}

# ------------------------------------------------------------
#
# ------------------------------------------------------------
def parse_row(row):
    rec = dict(zip(LIBGEN_CSV_FIELDS, row))
    for k in rec:
        if k in LIBGEN_FIELDS_PARSERS:
            parser, _ = LIBGEN_FIELDS_PARSERS[k]
            rec[k] = parser(rec[k])
    return rec


def display(rec):
    return "%s %s (%s,%s) [%s|%s]" % (
        rec["timeadded"].strftime("%Y-%m-%d"),
        rec["title"],
        rec["author"],
        rec["year"],
        rec["extension"],
        outils.string.fmt_num_bytes(int(rec["filesize"])),
    )


def filter_csv_file(
    csv_file=LIBGEN_CSV_FILE,
    date_from=None,
    date_until=None,
    fzf_file=LIBGEN_REZ_FILE,
    err_file=LIBGEN_ERR_FILE,
):
    rez = []
    errs = []
    t0 = time.time()
    with open(csv_file, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        for i, row in enumerate(reader, start=1):
            try:
                if i % 1000 == 0:
                    logger.info(outils.time.item_counter(t0, i))
                rec = parse_row(row)
                if date_from and rec["timeadded"] < date_from:
                    continue
                if date_until and rec["timeadded"] > date_from:
                    continue
                rez.append(display(rec))
            except (ValueError, KeyError, OverflowError) as e:
                errs.append(dict(zip(LIBGEN_CSV_FIELDS, row)))
            except:
                raise
    open(fzf_file,'w').write("\n".join(rez))
    open(err_file,'w').write("\n".join(map(str, errs)))
    return rez, errs


# ------------------------------------------------------------
#
# ------------------------------------------------------------
