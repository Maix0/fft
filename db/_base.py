import sqlite3

import config


def read_file(filename: str):
    with open(filename, "r") as f:
        return f.read()


def dict_factory(cursor, row) -> dict:
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class BaseDb:
    cur: sqlite3.Cursor
    con: sqlite3.Connection
    is_closed = False

    def __init__(self, filename=config.db_path):
        self.con = sqlite3.connect(filename)
        self.con.row_factory = dict_factory
        self.cur = self.con.cursor()

    # Management
    def initialize(self):
        self.create_table("scheme.sql")
        self.close()

    def commit(self):
        self.con.commit()

    def close(self):
        self.commit()
        self.con.close()
        self.is_closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _ = exc_type
        _ = exc_val
        _ = exc_tb
        if not self.is_closed:
            self.close()

    def __del__(self):
        if not self.is_closed:
            self.close()

    def create_table(self, sql_file: str):
        self.cur.executescript(read_file(sql_file))

    def raw_query(self, query, args):
        return self.cur.execute(query, args)
