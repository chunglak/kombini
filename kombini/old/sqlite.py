def insert_record(conn, table, record):
    q = "insert into {} ({}) values ({})".format(
        table, ",".join(record.keys()), ",".join("?" * len(record))
    )
    return conn.execute(q, tuple(record.values()))

def insert_records(conn, table, records):
    ks = list(records[0].keys())
    q = "insert into {} ({}) values ({})".format(
        table, ",".join(ks), ",".join("?" * len(ks))
    )
    return conn.executemany(q, [tuple(record[k] for k in ks) for record in records])

def update_record(conn, table, record, where_statement):
    fs = ",".join("%s=?" % k for k in record.keys())
    q = "update {} set {} where {}".format(table, fs, where_statement)
    return conn.execute(q, tuple(record.values()))
