import sqlite3
import os

class RequestDB(object):

    def __init__(self):
        self.path = os.path.join(os.getcwd(), "data", "requests.db")
        exists = os.path.exists(self.path)
        self.db = sqlite3.connect(self.path, check_same_thread=False,isolation_level=None)
        self.db.row_factory = sqlite3.Row
        if not exists:
            c = self.db.cursor()
            c.execute("""CREATE TABLE requests (
                id INTEGER PRIMARY KEY NOT NULL,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT DEFAULT "unverified" NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                verified_at TIMESTAMP DEFAULT NULL,
                decided_at TIMESTAMP DEFAULT NULL,
                decided_by TEXT DEFAULT NULL,
                reason TEXT DEFAULT NULL
            )""")
            c.close()

    def get_by_id(self, reqid):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE id = ?", (reqid,))
        req = c.fetchone()
        c.close()
        return req

    def get_by_key(self, key):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE key = ? COLLATE NOCASE", (key,))
        req = c.fetchone()
        c.close()
        return req

    def get_by_user(self, username):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE username = ? COLLATE NOCASE", (username,))
        reqs = c.fetchall()
        c.close()
        return reqs

    def get_by_email(self, email):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE email = ? COLLATE NOCASE", (email,))
        reqs = c.fetchall()
        c.close()
        return reqs

    def get_pending(self):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE status= \"pending\"")
        reqs = c.fetchall()
        c.close()
        return reqs

    def add(self, user, email, src):
        c = self.db.cursor()
        c.execute("""INSERT INTO requests (username, email, source) VALUES (?, ?, ?)""", (user, email,src))
        c.close()

    def verify(self, reqid):
        req = self.get_by_id(reqid)
        if not req:
            return False
        c = self.db.cursor()
        if req["status"] != "unverified":
            return False
        c.execute("""UPDATE requests SET status = "pending", verified_at = CURRENT_TIMESTAMP WHERE id = ?""", (req["id"],))
        c.close()
        return True

    def accept(self, reqid, source):
        req = self.get_by_id(reqid)
        if not req:
            return False
        c = self.db.cursor()
        c.execute("""UPDATE requests SET status = "accepted", decided_at = CURRENT_TIMESTAMP, decided_by = ? WHERE id = ?""",(source, req["id"]))
        c.close()
        return True

    def reject(self, reqid, source, reason):
        req = self.get_by_id(reqid)
        if not req:
            return False
        c = self.db.cursor()
        c.execute("""UPDATE requests SET status = "rejected", decided_at = CURRENT_TIMESTAMP,decided_by = ?, reason = ? WHERE id = ?""", (source, reason, req["id"]))
        c.close()
        return True

    def expires(self):
        c = self.db.cursor()
        c.execute("""DELETE FROM requests WHERE status = "unverified" AND datetime(created_at, "+1 day") < CURRENT_TIMESTAMP""")
        c.close()

class VerifyDB(object):

    def __init__(self):
        self.path = os.path.join(os.getcwd(), "data", "verify.db")
        exists = os.path.exists(self.path)
        self.db = sqlite3.connect(self.path, check_same_thread=False,isolation_level=None)
        self.db.row_factory = sqlite3.Row
        if not exists:
            c = self.db.cursor()
            c.execute("""CREATE TABLE keys (
                id INTEGER PRIMARY KEY,
                key TEXT NOT NULL UNIQUE,
                command TEXT NOT NULL,
                action_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            )""")
            c.close()

    def add(self, key, cmd, actid):
        if self.get_by_key(key):
            return False
        c = self.db.cursor()
        c.execute("INSERT INTO keys (key, command, action_id) VALUES (?, ?, ?)",(key, cmd, actid))
        c.close()
        return True

    def used(self, key):
        if not self.get_by_key(key):
            return False
        c = self.db.cursor()
        c.execute("DELETE FROM keys WHERE key = ?", (key,))
        c.close()
        return True

    def get_by_key(self, key):
        c = self.db.cursor()
        c.execute("SELECT * FROM keys WHERE key = ?", (key,))
        data = c.fetchone()
        c.close()
        return data

    def expires(self):
        c = self.db.cursor()
        c.execute("DELETE FROM keys WHERE datetime(created_at, \"+1 day\") < CURRENT_TIMESTAMP")
        c.close()
