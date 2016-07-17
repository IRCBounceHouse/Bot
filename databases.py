import sqlite3
import os

class RequestDB(object):

    def __init__(self):
        self.path = os.path.join(os.getcwd(), "data", "requests.db")
        exists = os.path.exists(self.path)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        if not exists:
            c = self.db.cursor()
            c.execute("""CREATE TABLE requests (
                id INTEGER PRIMARY KEY NOT NULL,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT DEFAULT "unverified" NOT NULL,
                server TEXT NOT NULL,
                port TEXT NOT NULL,
                ircnet TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                verified_at TIMESTAMP DEFAULT NULL,
                decided_at TIMESTAMP DEFAULT NULL,
                decided_by TEXT DEFAULT NULL,
                reason TEXT DEFAULT NULL,
                bncserver TEXT DEFAULT NULL
            )""")
            self.db.commit()
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

    def add(self, user, email, src, server, port, net):
        c = self.db.cursor()
        c.execute("""INSERT INTO requests (username, email, source, server,
            port, ircnet) VALUES (?, ?, ?, ?, ?, ?)""", (user, email,
            src, server, port, net))
        self.db.commit()
        c.close()

    def verify(self, reqid):
        req = self.get_by_id(reqid)
        if not req:
            return False
        c = self.db.cursor()
        if req["status"] != "unverified":
            return False
        c.execute("""UPDATE requests SET status = "pending",
            verified_at = CURRENT_TIMESTAMP WHERE id = ?""", (req["id"],))
        self.db.commit()
        c.close()
        return True

    def accept(self, reqid, source, bncserver):
        req = self.get_by_id(reqid)
        if not req:
            return False
        c = self.db.cursor()
        c.execute("""UPDATE requests SET status = "accepted", bncserver = ?,
            decided_at = CURRENT_TIMESTAMP, decided_by = ? WHERE id = ?""",
            (bncserver, source, req["id"]))
        self.db.commit()
        c.close()
        return True

    def reject(self, reqid, source, reason):
        req = self.get_by_id(reqid)
        if not req:
            return False
        c = self.db.cursor()
        c.execute("""UPDATE requests SET status = "rejected", decided_at = CURRENT_TIMESTAMP,
            decided_by = ?, reason = ? WHERE id = ?""", (source, reason, req["id"]))
        self.db.commit()
        c.close()
        return True

    def expires(self):
        c = self.db.cursor()
        c.execute("""DELETE FROM requests WHERE status = "unverified" AND
            datetime(created_at, "+1 day") < CURRENT_TIMESTAMP""")
        c.close()

class NetworkDB(object):

    def __init__(self):
        self.path = os.path.join(os.getcwd(), "data", "networks.db")
        exists = os.path.exists(self.path)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        if not exists:
            c = self.db.cursor()
            c.execute("""CREATE TABLE networks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                suspended INT DEFAULT 0 NOT NULL,
                suspendtype TEXT,
                suspendrson TEXT,
                suspended_at TIMESTAMP DEFAULT NULL,
                suspend_expires TIMESTAMP DEFAULT NULL,
                banned INT DEFAULT 0 NOT NULL,
                bantype TEXT,
                banrson TEXT,
                banned_at TIMESTAMP DEFAULT NULL
            )""")
            c.execute("""CREATE TABLE servers (
                id INTEGER PRIMARY KEY,
                address TEXT NOT NULL UNIQUE,
                network_id INT NOT NULL
            )""")
            c.execute("""CREATE TABLE defaults (
                id INTEGER PRIMARY KEY,
                address TEXT NOT NULL UNIQUE,
                port TEXT NOT NULL,
                network_id NOT NULL
            )""")
            self.db.commit()
            c.close()

    def get_net_by_id(self, netid):
        c = self.db.cursor()
        c.execute("SELECT * FROM networks WHERE id = ?", (netid,))
        net = c.fetchone()
        c.close()
        return net

    def get_net_by_name(self, name):
        c = self.db.cursor()
        c.execute("SELECT * FROM networks WHERE name = ? COLLATE NOCASE", (name,))
        net = c.fetchone()
        c.close()
        return net

    def get_net_by_server(self, addr):
        c = self.db.cursor()
        c.execute("SELECT network_id FROM servers WHERE ? LIKE address", (addr,))
        netid = c.fetchone()
        if not netid:
            c.close()
            return None
        c.close()
        return self.get_net_by_id(netid["network_id"])

    def get_net_defaults(self, netid):
        if not self.get_net_by_id(netid):
            return False
        c = self.db.cursor()
        c.execute("SELECT * FROM defaults WHERE network_id = ?", (netid,))
        defaults = c.fetchall()
        c.close()
        return defaults

    def addnet(self, name):
        if self.get_net_by_name(name):
            return False
        c = self.db.cursor()
        c.execute("INSERT INTO networks (name) VALUES (?)", (name,))
        self.db.commit()
        c.close()
        return True

    def addserver(self, netid, addr):
        if self.get_net_by_server(addr) or not self.get_net_by_id(netid):
            return False
        c = self.db.cursor()
        c.execute("INSERT INTO servers (address, network_id) VALUES (?, ?)",
            (addr, netid))
        self.db.commit()
        c.close()
        return True

    def defaultadd(self, netid, addr, port):
        if not self.get_net_by_id(netid):
            return False
        c = self.db.cursor()
        c.execute("SELECT * FROM defaults WHERE address = ?", (addr,))
        if c.fetchone():
            c.close()
            return False
        c.execute("INSERT INTO defaults (address, port, network_id) VALUES (?, ?, ?)",
            (addr, port, netid))
        self.db.commit()
        c.close()
        return True

    def suspend(self, netid, stype, reason, expires):
        if not self.get_net_by_id(netid):
            return False
        c = self.db.cursor()
        c.execute("""UPDATE networks SET suspended = 1, suspendtype = ?,
            suspendrson = ?, suspended_at = CURRENT_TIMESTAMP,
            suspend_expires = datetime(CURRENT_TIMESTAMP, ?) WHERE id = ?""",
            (stype, reason, "+"+expires, netid))
        self.db.commit()
        c.close()
        return True

    def unsuspend(self, netid):
        if not self.get_net_by_id(netid):
            return False
        c = self.db.cursor()
        c.execute("UPDATE networks SET suspended = 0 WHERE id = ?", (netid,))
        self.db.commit()
        c.close()
        return True

    def expires(self):
        c = self.db.cursor()
        c.execute("""UPDATE networks SET suspended = 0 WHERE suspended = 1 AND
            suspend_expires < CURRENT_TIMESTAMP""")
        c.close()

    def ban(self, netid, btype, reason):
        if not self.get_net_by_id(netid):
            return False
        c = self.db.cursor()
        c.execute("""UPDATE networks SET banned = 1, bantype = ?, banrson = ?,
            banned_at = CURRENT_TIMESTAMP WHERE id = ?""", (btype, reason, netid))
        self.db.commit()
        c.close()
        return True

    def unban(self, netid):
        if not self.get_net_by_id(netid):
            return False
        c = self.db.cursor()
        c.execute("UPDATE networks SET suspended = 0 WHERE id = ?", (netid,))
        self.db.commit()
        c.close()
        return True

class VerifyDB(object):

    def __init__(self):
        self.path = os.path.join(os.getcwd(), "data", "verify.db")
        exists = os.path.exists(self.path)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
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
            self.db.commit()
            c.close()

    def add(self, key, cmd, actid):
        if self.get_by_key(key):
            return False
        c = self.db.cursor()
        c.execute("INSERT INTO keys (key, command, action_id) VALUES (?, ?, ?)",
            (key, cmd, int(actid)))
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
        c.execute("DELETE FROM keys WHERE datetime(created_at, \"+1 day\") > CURRENT_TIMESTAMP")
        c.close()
