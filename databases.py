import sqlite3
import os

import utils

class RequestDB(object):

    def __init__(self):
        self.path = os.path.join(os.getcwd(), "data", "requests.db")
        exists = os.path.exists(self.path)
        self.db = sqlite3.connect(self.path)
        if not exists:
            c = self.db.cursor()
            c.execute("""CREATE TABLE requests (
                id INT PRIMARY KEY NOT NULL,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT DEFAULT "unverified" NOT NULL,
                server TEXT NOT NULL,
                port INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                verified_at TIMESTAMP DEFAULT NULL,
                decided_at TIMESTAMP DEFAULT NULL,
                bncserver TEXT DEFAULT NULL,
                ircnet TEXT DEFAULT NULL,
                key TEXT
            )""")
            c.commit()
            c.close()

    def get_by_id(self, reqid):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE id = %s", reqid)
        req = c.fetchone()
        c.close()
        return req

    def get_by_key(self, key):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE key = %s", key)
        req = c.fetchone()
        c.close()
        return req

    def get_by_user(self, username):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE username = %s", username)
        reqs = c.fetchall()
        c.close()
        return reqs

    def get_by_email(self, email):
        c = self.db.cursor()
        c.execute("SELECT * FROM requests WHERE email = %s", email)
        reqs = c.fetchall()
        c.close()
        return reqs

    def add(self, user, email, src, server, port, key, net):
        c = self.db.cursor()
        c.execute("""INSERT INTO requests (username, email, source, server,
            port, key, ircnet) VALUES (%s, %s, %s, %s, %s, %s, %s)""", (user,
            email, src, server, port, key, ircnet))
        c.commit()
        c.close()

    def verify(self, key):
        c = self.db.cursor()
        req = self.get_by_key(key)
        if not req:
            return False
        c.execute("""UPDATE requests SET status = "pending", key = NULL,
            verified_at = CURRENT_TIMESTAMP WHERE id = %s""", req["id"])
        c.commit()
        c.close()
        return True

    def accept(self, reqid, bncserver):
        c = self.db.cursor()
        req = self.get_by_id(reqid)
        if not req:
            return False
        c.execute("""UPDATE requests SET status = "accepted", bncserver = %s,
            decided_at = CURRENT_TIMESTAMP WHERE id = %s""", (bncserver, req["id"]))
        c.commit()
        c.close()
        return True

    def reject(self, reqid):
        c = self.db.cursor()
        req = self.get_by_id(reqid)
        if not req:
            return False
        c.execute("""UPDATE requests SET status = "rejected", decided_at = CURRENT_TIMESTAMP
            WHERE id = %s""", req["id"])
        c.commit()
        c.close()
        return True
