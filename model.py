import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json


def open_db(asn):
    return psycopg2.connect(asn)


def get_cursor(db):
    return db.cursor(cursor_factory=RealDictCursor)


def close_db(db):
    db.close()

class Channel(object):
    def __init__(self, id=None, url=None, display_name=None):
        self.id = id
        self.url = url
        self.display_name = display_name

    def insert(self, db):
        with get_cursor(db) as cur:
            cur.execute(
                "INSERT INTO channels (url, display_name) VALUES (%s, %s) RETURNING id",
                (self.url, self.display_name))
            self.id = cur.fetchone()['id']
        db.commit()

    def delete(self, db):
        with get_cursor(db) as cur:
            cur.execute("DELETE FROM channels WHERE id = %s", (self.id,))
        db.commit()

    @classmethod
    def get_channels(self, db):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, url, display_name FROM channels")
            return map(lambda d: Channel(**d), cur.fetchall())

    @classmethod
    def get_by_url(self, db, url):
        with get_cursor(db) as cur:
            cur.execute(
                "SELECT id, url, display_name FROM channels WHERE url = %s", (url,))
            res = cur.fetchone()
            return Channel(**res) if res is not None else None


class Notification(json.JSONEncoder):
    def __init__(self, id=None, channel=None, valid_from=None, valid_to=None, summary=None, description=None, location=None, channel_display_name=None):
        self.id = id
        self.channel = channel
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.summary = summary
        self.description = description
        self.location = location

        self.channel_display_name = channel_display_name

    def to_dict(self):
        return {
            "id": self.id,
            "valid_from": int(self.valid_from.timestamp()),
            "valid_to": int(self.valid_to.timestamp()),
            "summary": self.summary,
            "description": self.description,
            "location": self.location,
        }

    def insert(self, db):
        with get_cursor(db) as cur:
            cur.execute(
                "INSERT INTO notifications (channel, summary, description, location, valid_from, valid_to) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (self.channel, self.summary, self.description, self.location, self.valid_from, self.valid_to))
            self.id = cur.fetchone()['id']
        db.commit()

    def delete(self, db):
        with get_cursor(db) as cur:
            cur.execute("DELETE FROM notifications WHERE id = %s", (self.id,))
        db.commit()

    @classmethod
    def get_active_notifications_by_channel(self, db, channel):
        with get_cursor(db) as cur:
            current_time = datetime.now()
            send_earlier = timedelta(minutes=15)
            cur.execute(
                "SELECT n.id, n.channel, n.summary, n.description, n.location, n.valid_from, n.valid_to, c.display_name as channel_display_name FROM notifications as n LEFT JOIN channels as c ON n.channel = c.id WHERE n.valid_from < %s AND n.valid_to > %s AND c.id = %s",
                (current_time + send_earlier, current_time, channel.id))
            return map(lambda d: Notification(**d), cur.fetchall())

    @classmethod
    def get_notifications(self, db):
        with get_cursor(db) as cur:
            cur.execute(
                "SELECT n.id, n.channel, n.summary, n.description, n.location, n.valid_from, n.valid_to, c.display_name as channel_display_name FROM notifications as n LEFT JOIN channels as c ON n.channel = c.id")
            return map(lambda d: Notification(**d), cur.fetchall())


class User(object):
    def __init__(self, id=None, name=None, passhash=None, admin=False):
        self.id = id
        self.name = name
        self.passhash = passhash
        self.admin = admin

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    @classmethod
    def get_all(self, db):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, name, passhash, admin FROM users")
            result = cur.fetchall()
            return map(lambda u: User(**u), result)

    @classmethod
    def get_by_id(self, db, id):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, name, passhash, admin FROM users WHERE id=%s", (id,))
            result = cur.fetchone()
            return User(**result) if result is not None else None

    @classmethod
    def get_by_name(self, db, name):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, name, passhash, admin FROM users WHERE name=%s", (name,))
            result = cur.fetchone()
            return User(**result) if result is not None else None

    @classmethod
    def get_users(self, db):
        with get_cursor(db) as cur:
            cur.execute(
                "SELECT id, name, passhash, admin FROM users")
            return map(lambda d: User(**d), cur.fetchall())

    @classmethod
    def get_and_check(self, db, name, password):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, name, passhash, admin FROM users WHERE name=%s", (name,))
            result = cur.fetchone()
            if result is not None:
                user = User(**result)
                if user.check_password(password):
                    return user
                else:
                    return None
            else:
                return None

    def set_password(self, password):
        self.passhash = generate_password_hash(password)

    def insert(self, db):
        with get_cursor(db) as cur:
            cur.execute("INSERT INTO users (name, passhash, admin) VALUES (%s, %s, %s) RETURNING id", (self.name, self.passhash, self.admin))
            self.id = cur.fetchone()['id']
        db.commit()

    def update(self, db):
        with get_cursor(db) as cur:
            cur.execute("UPDATE users SET name=%s, passhash=%s, admin=%s WHERE id=%s", (self.name, self.passhash, self.admin, self.id))
        db.commit()

    def delete(self, db):
        with get_cursor(db) as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (self.id,))
        db.commit()

    def check_password(self, password):
        return check_password_hash(self.passhash, password)
