import json


def json_dump(obj, pth: str, **kwds):
    with open(pth, "w", encoding="utf8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, **kwds)
    # json.dump(obj, open(pth, "w"), indent=2, ensure_ascii=False, **kwds)


def json_load(pth: str):
    with open(pth, "r", encoding="utf8") as fh:
        return json.load(fh)
    # return json.load(open(pth, "r"))
