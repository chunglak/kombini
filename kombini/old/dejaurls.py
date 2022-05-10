import gzip
import os.path

import outils.logger as OuL

DEJA_URLS = os.path.expanduser("~/code/misc/misc/deja_urls.gz")


class DejaURLs:
    def __init__(self, logger=None):
        self.logger = OuL.default_logger(logger)
        self.urls = self.load_deja_urls()

    def load_deja_urls(self):
        if not os.path.isfile(DEJA_URLS):
            return set()
        lines = gzip.open(DEJA_URLS, "rt").read().split("\n")
        urls = set(s.strip() for s in lines if s)
        return urls

    def add_deja_urls(self, urls):
        urls = [url for url in urls if url not in self.urls]
        if urls:
            gzip.open(DEJA_URLS, "at").write("\n" + "\n".join(urls) + "\n")
            self.logger.info("Added %d links to deja" % len(urls))
            self.urls.update(urls)

    def notyet_url_p(self, url, remember=True):
        p = url not in self.urls
        if remember and p:
            # self.urls.add(url)
            self.add_deja_urls([url])
        return p

    def filter_notyet_urls(self, urls):
        return list(filter(self.notyet_url_p, urls))

    def filter_notyet_urls_dict(self, rs, k):
        def fil(r):
            return self.notyet_url_p(r[k])

        return list(filter(fil, rs))
