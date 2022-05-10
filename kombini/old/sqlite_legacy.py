#==============================================================================
"""
    name:           rml.tools.sqlite

    description:    interaction with SQLite3 (new version)

    started:        2011-10-12
    last:           2012-09-20
    py3 version:    2013-12-17
    pycharm:        2015-09-15

"""
#==============================================================================

#==============================================================================
#   Imports
#==============================================================================
#-System-----------------------------------------------------------------------
import datetime
import logging
import random
import sqlite3
import time
import typing as ty
#-Third party------------------------------------------------------------------
from dateutil.tz import tzutc
#-Own modules------------------------------------------------------------------
import outils.input as ouIn
import outils.logger as ouLo
#==============================================================================
#   Constants
#==============================================================================
COMMIT_TRIES = 3
COMMIT_LAG = 5
CONNECT_TIMEOUT = 20


class SQLiteConnectException(Exception):
    pass


#==============================================================================
# Data types
#==============================================================================

#==================================================
#   Converters / Adapters
#==================================================


def converter_datetime64(v: str):
    try:
        r = datetime.datetime.fromtimestamp(float(v))
        return r.replace(tzinfo=tzutc())
    except:
        return None


def adapter_datetime64(v):
    try:
        return time.mktime(v.utctimetuple())
    except:
        return None


def converter_datetime(v: str) -> ty.Union[datetime.datetime, None]:
    try:
        r = datetime.datetime.utcfromtimestamp(float(v))
        return r.replace(tzinfo=tzutc())
    except:
        return None


def adapter_datetime(v):
    try:
        return time.mktime(v.utctimetuple())
    except:
        return None


def converter_date(v):
    try:
        return datetime.date.fromordinal(int(v))
    except:
        return None


def adapter_date(v):
    try:
        return v.toordinal()
    except:
        return None


def converter_time(v):
    try:
        ns, tzn = v.split('#')
        h = int(ns / 3600)
        m = int((ns - h * 3600) / 60)
        s = int(ns - h * 3600 - m * 60)
        return datetime.time(h, m, s, tzinfo=gettz(tzn))
    except:
        raise
        return None


def adapter_time(v):
    try:
        return '%f#%s' % (v.hour * 3600 + v.minute * 60 + v.second,
                          v.tzname() if v.tzinfo else 'UTC')
    except:
        raise
        return None


def converter_bool(v):
    try:
        return {b'1': True, b'0': False}[v]
    except:
        raise
        return None


def adapter_bool(v):
    try:
        return {True: '1', False: '0'}[v]
    except:
        raise
        return None


#==================================================
#
#==================================================
def register_datatype(typename: str, converter: ty.Callable, type,
                      adapter: ty.Callable):
    sqlite3.register_converter(typename, converter)
    sqlite3.register_adapter(type, adapter)


def register_def_datatypes() -> None:
    DEF_ADCONV_DIC = {
        'datetime': {
            'converter': converter_datetime,
            'adapter': adapter_datetime,
            'type': datetime.datetime,
        },
        'date': {
            'converter': converter_date,
            'adapter': adapter_date,
            'type': datetime.date,
        },
        'time': {
            'converter': converter_time,
            'adapter': adapter_time,
            'type': datetime.time,
        },
        'bool': {
            'converter': converter_bool,
            'adapter': adapter_bool,
            'type': bool,
        },
    }

    for tn in DEF_ADCONV_DIC:
        rec = DEF_ADCONV_DIC[tn]
        register_datatype(typename=tn,
                          converter=rec['converter'],
                          adapter=rec['adapter'],
                          type=rec['type'])


#==============================================================================
#
# SQLiteConnect class
#
#==============================================================================


class SQLiteConnect:
    def __init__(self,
                 fn: ty.Optional[str] = None,
                 logger: ty.Optional[logging.Logger] = None):
        self.logger = ouLo.default_logger(logger)
        try:
            self.conn = sqlite3.connect(fn if fn else ':memory:',
                                        detect_types=sqlite3.PARSE_DECLTYPES,
                                        timeout=CONNECT_TIMEOUT)
        except:
            raise
        self.conn.row_factory = sqlite3.Row  #access columns by index AND name
        register_def_datatypes()
        self.cur = self.conn.cursor()
        self.commit_flag = True

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def close(self) -> None:
        self.commit()
        self.cur.close()
        self.conn.close()

    #==================================================
    #   Convenience functions
    #==================================================

    def commit(self):
        #in case the DB is locked we try COMMIT_TRIES times
        #with a time spacing of COMMIT_LAG
        tries = 0
        while tries <= COMMIT_TRIES:
            try:
                self.conn.commit()
                return
            except sqlite3.OperationalError:
                self.logger.warning('Could not commit changes (try #%d)' \
                                    % tries)
                tries += 1
                time.sleep(COMMIT_LAG * tries)
        raise SQLiteConnectException

    def rollback(self):
        self.conn.rollback()

    def col_names(self):
        """
        Return list of column names of last query
        """
        d = self.cur.description
        if d:
            return [rec[0] for rec in d]
        else:
            return None

    def execute(self, q, p=None, return_data=False):
        tries = 0
        while True:
            try:
                if p:
                    self.cur.execute(q, p)
                else:
                    self.cur.execute(q)
            except sqlite3.IntegrityError:
                raise
            except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
                self.logger.error(e)
                tries += 1
                if tries >= 3:
                    print('%s %s' % (q, p))
                    raise
                st = random.randrange(1, 8)
                self.logger.debug('Retrying in %ds' % st)
                time.sleep(st)
            else:
                break
        if self.commit_flag: self.commit()
        if return_data:
            return self.cur.fetchall()
        return self.cur.rowcount

    def executemany(self, q, p=None):
        tries = 0
        while True:
            try:
                if p:
                    self.cur.executemany(q, p)
                else:
                    self.cur.executemany(q)
            except sqlite3.IntegrityError:
                raise
            except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
                self.logger.error(e)
                tries += 1
                if tries >= 3:
                    print('%s %s' % (q, p))
                    raise
                st = random.randrange(1, 8)
                self.logger.debug('Retrying in %ds' % st)
                time.sleep(st)
            else:
                break
        if self.commit_flag: self.commit()
        return self.cur.rowcount

    def executescript(self, s):
        self.cur.executescript(s)
        if self.commit_flag: self.commit()
        return self.cur.rowcount

    def vacuum(self):
        self.execute('vacuum')

    #==================================================
    #   SQL requests generators
    #==================================================

    def create_insert_sql_request(self, table, inst, ignore=False,
                                  force=False):
        """
        ::string,dict,[bool]->(string,list)

        Generates elements of sql insert request from
        keys/values of dict inst
        ignore==True=>errors on insert are warnings only, not errors
        """
        kl = list(inst)
        if ignore:
            conf = 'or ignore'
        elif force:
            conf = 'or replace'
        else:
            conf = ''
        rez = 'insert %s into %s(%s) values (%s)' % (conf, table, ','.join(
            [str(k) for k in kl]), ','.join(['?'] * len(kl)))
        return (rez,tuple([inst[k] \
            if type(inst[k])==str else inst[k] for k in kl]))
        # return (rez,tuple([unicode(inst[k],encoding='utf8') \
        #     if type(inst[k])==str else inst[k] for k in kl]))

    def create_select_sql_request(self, table, fields):
        """
        ::string,list->string
        """
        return 'select %s from %s' % (','.join(['%s' % f for f in fields])
                                      if fields else '*', table)

    def create_update_sql_request(self, table, inst, conditions):
        ks = list(inst.keys())
        s = ','.join(['%s=?' % k for k in ks])
        v = [inst[k] for k in ks]
        c, v2 = self.create_conditions_sql_request(conditions)
        sql = 'update %s set %s %s' % (table, s, c)
        v = list(v) + list(v2)
        return sql, v

    def create_conditions_sql_request(self, conditions):
        """
        ::list([c1,c2,val])->string
        conditions are 'c1 c2 val' literally
        """
        if not conditions: return '', ()
        rez='where %s' % ' and '.join([('%s %s ?' % \
            (x[0],x[1] if (x[-1] is not None) else 'is')) \
            if type(x) is not str else x for x in conditions])
        vl = [x[-1] for x in conditions if type(x) is not str]
        return (rez, vl)

    #==================================================
    #   DB interaction functions
    #==================================================

    def insert_record(self, table, inst, ignore=False, force=False):
        """
        ::string,dict,[bool],[bool]->IO int
        Inserts record held by dict inst in table table
        """
        rez = self.create_insert_sql_request(table,
                                             inst,
                                             ignore=ignore,
                                             force=force)
        return self.execute(rez[0], rez[1])

    def insert_many(self, table, inst, ignore=False, force=False):
        """
        ::string,list(dict),[bool]->IO int
        """
        if not inst:
            return -1
        fl = list(inst[0])  #get field names from 1st record
        if ignore:
            conf = 'or ignore'
        elif force:
            conf = 'or replace'
        else:
            conf = ''
        q1 = 'insert %s into %s(%s) values(%s)' % (conf, table, ','.join(
            [str(f) for f in fl]), ','.join(['?'] * len(fl)))
        vl=[[rec[f] if type(rec[f])==str else rec[f] \
            for f in fl] for rec in inst] #make a list of lists
        r = self.executemany(q1, vl)
        if r == -1:
            return 0
        return r

    def retrieve_record(self,
                        table,
                        fields=None,
                        field=None,
                        conditions=None,
                        limit=None,
                        to_dict=False):
        """
        ::string,[list(string)],[string],[list(tuple(3))],[int|None],[bool]->
            IO string|list|dict|None
        Retrieves record in table with fields in fields (list)
        result=
            string  if field and limit==1
            dict    if to_dict==True
            list    otherwise
            None    if error
        """
        if field:
            fields = [field]
        #elif fields==None:
        #    return None #No field specified
        rez = self.create_select_sql_request(table, fields)
        if conditions:
            rez2, vl = self.create_conditions_sql_request(conditions)
            rez = rez + ' ' + rez2
            if limit:
                rez += ' limit %s' % limit
            self.execute(rez, vl)
        else:
            if limit:
                rez += ' limit %s' % limit
            self.execute(rez)
        t = self.cur.fetchall()
        if t:
            if fields and len(fields) == 1:  #only one field
                rez = [x[0] for x in t]  #format (r1->f,r2->f...)
            elif to_dict:
                rez = [dict(x) for x in t]
            else:
                rez = [list(x)
                       for x in t]  #format ((r1->f1,r1->f2...),(r2->f1,...))
            if limit == 1:  #we return just scalar instead of list
                rez = rez[0]
            return rez
        return None

    def retrieve_id(self, table, idfield, conditions=None):
        return self.retrieve_record(table=table,field=idfield,conditions=\
            conditions,limit=1)

    def delete_record(self, table, conditions):
        """
        ::string,list(tuple(3))->IO ()
        """
        rez = 'delete from %s' % table
        rez2 = self.create_conditions_sql_request(conditions)
        if rez2:
            return self.execute(rez + ' ' + rez2[0], rez2[1])
        else:
            return self.execute(rez)

    def execute_statements(self, st, returns=False):
        """
        ::string|list->IO ()|list
        Executes a list of statements in st
        """
        if type(st) != type([]):  # if there's only one statement in st
            st = [st]  # then make a list of it
        for s in st:
            self.execute(s)
        self.commit()
        if returns:
            t = self.cur.fetchall()
            return t

    def update_record(self, table, inst, conditions, limit=0):
        sql, vl = self.create_update_sql_request(table=table,
                                                 inst=inst,
                                                 conditions=conditions)
        if limit:
            sql += ' limit %d' % limit
        return self.execute(sql, vl)

    #==================================================
    #   Misc DB lookup functions
    #==================================================

    def minmax_value(self, minmax, table, variable, conditions=None):
        """
        ::'min'|'max',string,string,list(tuple(3))->IO scalar|None
        Returns min or max value for a variable in a table
        conditions is a list of triplets (var,condition,value)
        eg (dt,">",date(2008,1,1))
        """
        sql = 'select %s(%s) from %s' % (minmax, variable, table)
        if conditions:
            sql2, vl = self.create_conditions_sql_request(conditions)
            sql = sql + ' ' + sql2
            self.execute(sql, tuple(vl))
        else:
            self.execute(sql)
        t = self.cur.fetchone()
        return t[0] if t else None

    def check_existence(self, table, conditions):
        sql2, vl = self.create_conditions_sql_request(conditions=conditions)
        sql = 'select exists(select 1 from %s %s limit 1)' % (table, sql2)
        self.execute(sql, tuple(vl))
        t = self.cur.fetchone()
        return True if t[0] else False

    #==================================================
    #   Table creation
    #==================================================

    def make_table(self, table_name, details, confirm=True):
        """
        ::string,list(string),[bool]->IO ()
        """
        if confirm:
            do_confirm=ouIn.yes_or_no('Are you sure you want to reset %s?' % \
                table_name)
        else:
            do_confirm = True

        if do_confirm:
            st = [
                'drop table if exists %s' % table_name,
                'create table %s(%s)' % (table_name, ','.join(details))
            ]
            self.execute_statements(st)

    def make_index(self, idx_name, tbl_name, cols, unique=True):
        q = 'create %s index %s on %s (%s)' % (
            'unique' if unique else '', idx_name, tbl_name, ','.join(cols))
        self.execute(q)
