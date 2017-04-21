from flask import Flask, jsonify
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor

db = "dbname=gulasch_notifier"
conn = psycopg2.connect(db)

cur = conn.cursor(cursor_factory=RealDictCursor)

app = Flask(__name__)

class Notification(json.JSONEncoder):
    def __init__(self, id, valid_from, valid_to, summary, description, location):
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
        cur.execute("INSERT INTO notifications (summary, description, location, valid_from, valid_to) VALUES (%s, %s, %s, %s, %s) RETURNING id", self.summary, self.description, self.location, self.valid_from, self.valid_to)
        self.id = cur.fetchone()['id']

    @classmethod
    def get_active_notifications(self):
        current_time = int(time.time() * 1000)
        cur.execute("SELECT id, summary, description, location, valid_from, valid_to FROM notifications WHERE valid_from < %s AND valid_to > %s", (current_time + 30000, current_time))
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

if __name__ == "__main__":
    app.run(debug=True)
