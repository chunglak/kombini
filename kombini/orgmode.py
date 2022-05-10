import re

from outils.logger import default_logger


class OrgParse:
    def __init__(self, ls, logger=None):
        self.logger = default_logger(logger)
        self.data = OrgParse.orgparse(ls, logger=self.logger)

    def find_header(self, hs, root=None, startswith=False):
        if root is None:
            root = self.data
        for c in root["children"]:
            if (startswith and c["name"].startswith(hs[0])) or c["name"] == hs[0]:
                if len(hs) == 1:
                    return c
                else:
                    r = self.find_header(hs[1:], root=c, startswith=startswith)
                    if r:
                        return r
        return None

    def find_date(self, ls):
        for l in ls:
            m = re.search("\[(\d{4}-\d{2}-\d{2}.*)\]", l)
            if m:
                s = m.groups()[0]
                from dateutil.parser import parse

                return parse(s)
        return None

    @classmethod
    def load_from_file(cls, fn, logger=None):
        ls = list(filter(None, [l.strip() for l in open(fn, "r")]))
        return cls(ls, logger=logger)

    @staticmethod
    def orgparse(ls, logger=None):
        def clean_parent(node):
            del node["parent"]
            for c in node["children"]:
                clean_parent(c)

        logger = default_logger(logger)
        root = {"name": "", "level": 0, "children": [], "lines": [], "parent": None}
        current = root
        for l in ls:
            l = l.strip()
            if not l:
                continue
            m = re.match("(\*+)\s+(.+)", l)
            if m:
                fs = m.groups()
                level, name = len(fs[0]), fs[1].strip()
                # print('%s [%d]' % (name,level))
                node = {
                    "name": name,
                    "level": level,
                    "children": [],
                    "lines": [],
                    "parent": None,
                }
                if level == current["level"]:
                    parent = current["parent"]
                    node["parent"] = parent
                    parent["children"].append(node)
                elif level > current["level"]:
                    node["parent"] = current
                    current["children"].append(node)
                else:  # level<current.level
                    while current["level"] > level:
                        current = current["parent"]
                    node["parent"] = current["parent"]
                    node["parent"]["children"].append(node)
                current = node
            else:
                current["lines"].append(l)

        clean_parent(root)
        return root
