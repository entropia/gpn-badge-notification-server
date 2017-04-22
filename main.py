import flask
from flask import Flask, jsonify, render_template, request, redirect, url_for
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(flask.g, 'db_conn'):
        db = "dbname=gulasch_notifier"
        conn = psycopg2.connect(db)
        flask.g.db_conn = conn
    return flask.g.db_conn

def get_cursor():
    db = get_db()
    return db.cursor(cursor_factory=RealDictCursor)

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(flask.g, 'db_conn'):
        flask.g.db_conn.close()

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

    def insert(self):
        with get_cursor() as cur:
            cur.execute("INSERT INTO notifications (summary, description, location, valid_from, valid_to) VALUES (%s, %s, %s, %s, %s) RETURNING id", (self.summary, self.description, self.location, self.valid_from, self.valid_to))
            self.id = cur.fetchone()['id']
        get_db().commit()

    def delete(self):
        with get_cursor() as cur:
            cur.execute("DELETE FROM notifications WHERE id = %s", (self.id, ))
        get_db().commit()

    @classmethod
    def get_active_notifications(self):
        with get_cursor() as cur:
            current_time = datetime.now()
            send_earlier = timedelta(seconds=30)
            cur.execute("SELECT id, summary, description, location, valid_from, valid_to FROM notifications WHERE valid_from < %s AND valid_to > %s", (current_time + send_earlier, current_time))
            return map(lambda d: Notification(**d), cur.fetchall())

    @classmethod
    def get_notifications(self):
        with get_cursor() as cur:
            cur.execute("SELECT id, summary, description, location, valid_from, valid_to FROM notifications")
            return map(lambda d: Notification(**d), cur.fetchall())
        

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/api/poll")
def poll():
    return jsonify({
                'server_time': int(time.time() * 1000),
                'notifications': map(Notification.to_dict, Notification.get_active_notifications())
            })

date_fmt = '%c'

@app.route("/manage")
def list_notifications():
    notifications = Notification.get_notifications()
    now = datetime.now()
    return render_template('notifications_list.html', notifications=notifications, current_time=now.strftime(date_fmt))

@app.route("/manage/add", methods=['POST'])
def new_notification():
    valid_from = datetime.strptime(request.form['valid_from'], date_fmt)
    valid_to = datetime.strptime(request.form['valid_to'], date_fmt)
    new_notification = Notification(summary=request.form['summary'], description=request.form['description'], valid_from=valid_from, valid_to=valid_to)
    new_notification.insert()
    return redirect(url_for('list_notifications'))

@app.route("/manage/delete", methods=['POST'])
def delete_notification():
    Notification(id=int(request.form['id'])).delete()
    return redirect(url_for('list_notifications'))

if __name__ == "__main__":
    app.run(debug=True)
