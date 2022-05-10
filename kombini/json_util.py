import json


def json_dump(obj, pth: str, **kwds):
    json.dump(obj, open(pth, "w"), indent=2, ensure_ascii=False, **kwds)


def json_load(pth: str):
    return json.load(open(pth, "r"))
