import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json


def open_db():
    db = "dbname=gulasch_notifier"
    return psycopg2.connect(db)


def get_cursor(db):
    return db.cursor(cursor_factory=RealDictCursor)


def close_db(db):
    db.close()


class Notification(json.JSONEncoder):
    def __init__(self, id=None, valid_from=None, valid_to=None, summary=None, description=None, location=None):
        self.id = id
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.summary = summary
        self.description = description
        self.location = location

    def to_dict(self):
        return {
            "id": self.id,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "summary": self.summary,
            "description": self.description,
            "location": self.location,
        }

    def insert(self, db):
        with get_cursor(db) as cur:
            cur.execute(
                "INSERT INTO notifications (summary, description, location, valid_from, valid_to) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (self.summary, self.description, self.location, self.valid_from, self.valid_to))
            self.id = cur.fetchone()['id']
        db.commit()

    def delete(self, db):
        with get_cursor(db) as cur:
            cur.execute("DELETE FROM notifications WHERE id = %s", (self.id,))
        db.commit()

    @classmethod
    def get_active_notifications(self, db):
        with get_cursor(db) as cur:
            current_time = datetime.now()
            send_earlier = timedelta(seconds=30)
            cur.execute(
                "SELECT id, summary, description, location, valid_from, valid_to FROM notifications WHERE valid_from < %s AND valid_to > %s",
                (current_time + send_earlier, current_time))
            return map(lambda d: Notification(**d), cur.fetchall())

    @classmethod
    def get_notifications(self, db):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, summary, description, location, valid_from, valid_to FROM notifications")
            return map(lambda d: Notification(**d), cur.fetchall())


class User(object):
    def __init__(self, id=None, name=None, passhash=None):
        self.id = id
        self.name = name
        self.passhash = passhash

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
            cur.execute("SELECT id, name, passhash FROM users")
            result = cur.fetchall()
            return map(lambda u: User(**u), result)

    @classmethod
    def get_by_id(self, db, id):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, name, passhash FROM users WHERE id=%s", (id,))
            result = cur.fetchone()
            return User(**result) if result is not None else None

    @classmethod
    def get_by_name(self, db, name):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, name, passhash FROM users WHERE name=%s", (name,))
            result = cur.fetchone()
            return User(**result) if result is not None else None

    @classmethod
    def get_and_check(self, db, name, password):
        with get_cursor(db) as cur:
            cur.execute("SELECT id, name, passhash FROM users WHERE name=%s", (name,))
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
            cur.execute("INSERT INTO users (name, passhash) VALUES (%s, %s) RETURNING id", (self.name, self.passhash))
            self.id = cur.fetchone()['id']
        db.commit()

    def update(self, db):
        with get_cursor(db) as cur:
            cur.execute("UPDATE users SET name=%s, passhash=%s WHERE id=%s", (self.name, self.passhash, self.id))
        db.commit()

    def delete(self, db):
        with get_cursor(db) as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (self.id,))
        db.commit()

    def check_password(self, password):
        return check_password_hash(self.passhash, password)
