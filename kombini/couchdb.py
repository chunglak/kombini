import collections
import json

import requests

import outils.logger

SC_OK = 200
SC_CREATED = 201
SC_ACCEPTED = 202
SC_BAD_REQUEST = 400
SC_UNAUTHORIZED = 401
SC_NOT_FOUND = 404
SC_CONFLICT = 409
SC_PRECONDITION_FAILED = 412

DEFAULT_URL = "http://127.0.0.1:5984"

USERS_DB = "_users"

Cdbr = collections.namedtuple("CDB_Response", ["ok", "data"], defaults=[False, None])

# Help translate curl → requests
# https://curl.trillworks.com/


def defurl(url):
    return url if url else DEFAULT_URL


class CouchDB:
    def __init__(self, url=None, name=None, password=None, logger=None):
        self.logger = outils.logger.default_logger(logger)
        self.url = defurl(url)
        self.name = name
        self.password = password
        self.auth = (self.name, self.password) if self.name else None

    # ------------------------------
    @classmethod
    def set_initial_admin(
        cls, name, password, nodename="_local", url=None, logger=None
    ):
        logger = outils.logger.default_logger(logger)
        url = defurl(url)
        furl = "%s/_node/%s/_config/admins/%s" % (url, nodename, name)
        r = requests.put(furl, data='"%s"' % password)
        sc = r.status_code
        if sc == SC_OK:
            logger.info("Created admin user %s", name)
            return cls(url=url, name=name, password=password)
        elif sc == SC_UNAUTHORIZED:
            logger.error("Cannot create new admin user. Other admin users exist")
            return None
        else:
            raise Exception("%s [%s]" % (sc, r.reason))

    # ==============================
    # Convenience functions
    # ==============================
    def curl(self, action, dbname=None, aurl=None, **kwargs):
        url = "%s/%s" % (self.url, dbname) if dbname else self.url
        url = "%s/%s" % (url, aurl) if aurl else url
        if action == "get":
            return requests.get(url, auth=self.auth, **kwargs)
        elif action == "put":
            return requests.put(url, auth=self.auth, **kwargs)
        elif action == "delete":
            return requests.delete(url, auth=self.auth, **kwargs)
        elif action == "post":
            return requests.post(url, auth=self.auth, **kwargs)
        else:
            raise Exception("Unkown action %s" % action)

    # ==============================
    # Server-related
    # ==============================
    def server_api_all_dbs(self):
        r = self.curl("get", aurl="_all_dbs")
        sc = r.status_code
        if sc == SC_OK:
            return Cdbr(ok=True, data={"r": r, "data": r.json()})
        else:
            return Cdbr(ok=False, data={"r": r})

    # ==============================
    # DB-related
    # ==============================
    def db_api_create(self, dbname, secure_db_user=None):
        r = self.curl("put", dbname=dbname)
        sc = r.status_code
        if sc == SC_CREATED:
            self.logger.info("Created database %s", dbname)
            if secure_db_user:
                r2 = self.db_add_authorization(dbname, secure_db_user)
                if not r2.ok:
                    return Cdbr(ok=False, data={"r": r2, "rr": r})
            return Cdbr(ok=True, data={"r": r})
        else:
            return Cdbr(ok=False, data={"r": r})

    def db_api_delete(self, dbname):
        r = self.curl("delete", dbname=dbname)
        sc = r.status_code
        if sc == SC_OK:
            self.logger.info("Deleted database %s", dbname)
            return Cdbr(ok=True, data={"r": r})
        else:
            return Cdbr(ok=False, data={"r": r})

    def db_security_doc(self, dbname):
        return self.doc_api_get(dbname, doc_id="_security")

    def db_save_security_doc(self, dbname, doc):
        doc["_id"] = "_security"
        return self.doc_api_put(dbname, doc)

    def db_add_authorization(self, dbname, name, userclass="member", exclusive=False):
        userclass = userclass.lower()
        assert userclass in ["admin", "member"]
        userclass += "s"
        r = self.db_security_doc(dbname)
        if not r.ok:
            return r
        doc = r.data["data"]
        if not doc:
            doc = {
                "admins": {"names": [], "roles": []},
                "members": {"names": [], "roles": []},
            }
        if exclusive:
            doc[userclass]["names"] = [name]
        else:
            names = doc[userclass]["names"] if 'names' in doc[userclass] else []
            if name not in names:
                names.append(name)
        return self.db_save_security_doc(dbname, doc)

    def db_remove_authorization(self, dbname, name, userclass="member"):
        userclass = userclass.lower()
        assert userclass in ["admin", "member"]
        userclass += "s"
        r = self.db_security_doc(dbname)
        if not r.ok:
            if r.data["r"].status_code != SC_NOT_FOUND:
                return r
            return Cdbr(ok=True)
        else:
            doc = r.data["data"]
        names = doc[userclass]["names"]
        if name in names:
            names.remove(name)
            return self.db_save_security_doc(dbname, doc)
        else:
            return Cdbr(ok=True)

    def db_exists_p(self, dbname):
        r = self.curl("get", dbname=dbname)
        return r.status_code == SC_OK

    # ==============================
    # Doc-related
    # ==============================
    def doc_api_bulk_docs(self, dbname, docs, new_edits=True):
        data = {"docs": docs, "new_edits": new_edits}
        headers = {"Content-Type": "application/json"}
        r = self.curl(
            "post",
            dbname=dbname,
            aurl="_bulk_docs",
            # data=data,
            data=json.dumps(data),
            headers=headers,
        )
        sc = r.status_code
        if sc == SC_CREATED:
            return Cdbr(ok=True, data={"r": r})
        else:
            return Cdbr(ok=False, data={"r": r})

    def doc_api_all_docs(self, dbname, raw=False, include_docs=True):
        params = {"include_docs": include_docs}
        r = self.curl("get", dbname=dbname, aurl="_all_docs", params=params)
        sc = r.status_code
        if sc == SC_OK:
            if include_docs and not raw:
                return Cdbr(
                    ok=True,
                    data={"r": r, "data": [row["doc"] for row in r.json()["rows"]]},
                )
            else:
                return Cdbr(ok=True, data={"r": r})
        else:
            return Cdbr(ok=False, data={"r": r})

    def doc_api_put(self, dbname, doc):
        if "_id" not in doc:
            self.logger.error("No _id in doc")
            return Cdbr(ok=False)
        headers = {"Content-Type": "application/json"}
        r = self.curl(
            "put", dbname=dbname, aurl=doc["_id"], data=json.dumps(doc), headers=headers
        )
        sc = r.status_code
        if sc in (SC_OK, SC_CREATED):
            return Cdbr(ok=True, data={"r": r})
        else:
            return Cdbr(ok=False, data={"r": r})

    def doc_api_get(self, dbname, doc=None, doc_id=None):
        _id = doc_id if doc_id else doc["_id"]
        r = self.curl("get", dbname=dbname, aurl=_id)
        sc = r.status_code
        if sc == SC_OK:
            return Cdbr(ok=True, data={"r": r, "data": r.json()})
        else:
            return Cdbr(ok=False, data={"r": r})

    def doc_api_delete(self, dbname, doc=None, doc_id=None):
        odoc = self.doc_api_get(dbname=dbname, doc=doc, doc_id=doc_id)
        if not odoc:
            return None
        r = self.curl(
            "delete", dbname=dbname, aurl=odoc["_id"], params={"rev": odoc["_rev"]}
        )
        sc = r.status_code
        if sc == SC_OK:
            return Cdbr(ok=True, data={"r": r})
        else:
            return Cdbr(ok=False, data={"r": r})

    # ==============================
    # User-related
    # ==============================
    def user_id(self, name):
        return "org.couchdb.user:%s" % name

    def user_create(self, name, password):
        if USERS_DB not in self.server_api_all_dbs():
            self.logger.info("No %s db: creating", USERS_DB)
            self.db_api_create(USERS_DB)
        doc = {
            "_id": self.user_id(name),
            "name": name,
            "password": password,
            "roles": [],
            "type": "user",
        }
        return self.doc_api_put(USERS_DB, doc)

    def user_delete(self, name):
        if USERS_DB not in self.server_api_all_dbs():
            self.logger.info("No %s db", USERS_DB)
            return None
        return self.doc_api_delete(USERS_DB, doc_id=self.user_id(name))

    def user_change_password(self, name, password, create_if_not_exist=True):
        r = self.doc_api_get(USERS_DB, doc_id=self.user_id(name))
        if not r.ok:
            if r.data["r"].status_code != SC_NOT_FOUND:
                return Cdbr(ok=False, data={"r": r})
            doc = None
        else:
            doc = r.data["data"]
        if not doc:
            if create_if_not_exist:
                self.logger.info("User %s does not exist. Creating", name)
                r = self.user_create(name, password)
                if not r.ok:
                    return r
                return self.user_change_password(
                    name=name, password=password, create_if_not_exist=False
                )
            else:
                self.logger.info("User %s does not exist" % name)
                return Cdbr(ok=False)
        doc["password"] = password
        return self.doc_api_put(USERS_DB, doc)
