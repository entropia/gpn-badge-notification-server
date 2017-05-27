#!/usr/bin/env python3
from functools import wraps
import flask
from flask import Flask, render_template, request, redirect, url_for, Response, abort
from flask_login import LoginManager, login_user, logout_user, login_required
import flask_login.utils
import time
import urllib.parse
import requests
import dateutil.parser
from pytz import reference
from werkzeug.local import LocalProxy

from model import *

app = Flask(__name__)
app.config.from_pyfile('settings.py')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(flask.g, 'db_conn'):
        flask.g.db_conn = open_db(app.config.get("DB_DSN"))
    return flask.g.db_conn


@app.teardown_appcontext
def teardown(error):
    """Closes the database again at the end of the request."""
    if hasattr(flask.g, 'db_conn'):
        close_db(flask.g.db_conn)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get_by_id(get_db(), int(user_id))
    except ValueError:
        return None

def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask_login.utils.current_user.is_anonymous or not flask_login.utils.current_user.admin:
            return login_manager.unauthorized()
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.get_and_check(get_db(), request.form['name'], request.form['password'])
        if user is not None:
            login_user(user)
            next = flask.request.args.get('next')
            return flask.redirect(flask.url_for(next or 'list_notifications'))
        else:
            return flask.render_template('login.html'), 403
    else:
        return flask.render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return flask.redirect(flask.url_for('login'))

@app.route("/api/channel/<channel_url>")
def poll(channel_url):
    ret = str(int(time.time())) + "\n"
    channel = Channel.get_by_url(get_db(), channel_url)
    ret += channel.display_name + "\n"
    if channel is None:
        abort(404)
    for noti in list(map(Notification.to_dict, Notification.get_active_notifications_by_channel(get_db(), channel))):
        ret += urllib.parse.urlencode(noti) + '\n'
    return Response(ret, mimetype='text/plain')


@app.route("/api/schedule")
def schedule_index():
    ret = ""
    fp = requests.get(app.config.get('SCHEDULE_JSON')).json()['schedule']['conference']['days']
    now = datetime.now().replace(tzinfo=reference.LocalTimezone())

    ##debug
    now = now.replace(day=26, hour=1)
    ##debug

    current_day = None
    for day in fp:
        start = dateutil.parser.parse(day['day_start'])
        end = dateutil.parser.parse(day['day_end'])
        print(start)
        print(now)
        if start <= now <= end:
            current_day = day
            break
    if current_day is None:
        return "no room today"
    for r in day['rooms']:
        ret += r
        ret += '\n'
    return Response(ret, mimetype='text/plain')


@app.route("/api/schedule/<room>")
def schedule(room):
    fp = requests.get(app.config.get('SCHEDULE_JSON')).json()['schedule']['conference']['days']
    now = datetime.now().replace(tzinfo=reference.LocalTimezone())

    ##debug
    now = now.replace(day=26, hour=14)
    ##debug

    ret = str(int(now.timestamp())) + "\n"
    ret += room + "\n"
    current_day = None
    for day in fp:
        start = dateutil.parser.parse(day['day_start'])
        end = dateutil.parser.parse(day['day_end'])
        if start <= now <= end:
            current_day = day
            break
    if current_day is None:
        return Response(ret, mimetype='text/plain')
    if room not in day['rooms']:
        abort(404)
    sched = current_day['rooms'][room]
    for thing in sched:
        send_earlier = timedelta(minutes=15)
        d = dateutil.parser.parse(thing['date'])
        dur = thing['duration'].split(':')
        valid_to = d + timedelta(hours=int(dur[0]), minutes=int(dur[1]))
        if now > valid_to or now < (d - send_earlier):
            continue
        ret += urllib.parse.urlencode({"id": thing['id'], 'summary': thing['title'], 'description': thing['subtitle'],
                                       'location': thing['room'],
                                       'valid_from': int(d.timestamp()),
                                       'valid_to': int(valid_to.timestamp())}) + '\n'
    return Response(ret, mimetype='text/plain')


date_fmt = '%c'


@app.route("/manage")
@login_required
def list_notifications():
    notifications = Notification.get_notifications(get_db())
    channels = list(Channel.get_channels(get_db()))
    now = datetime.now()
    return render_template('notifications_list.html', notifications=notifications, channels=channels,
                           current_time=now.strftime(date_fmt))

@app.route("/users")
@requires_admin
def manage_users():
    users = User.get_users(get_db())
    return render_template('users_list.html', users=users)

@app.route("/users/add", methods=['POST'])
@requires_admin
def new_user():
    name = request.form['name']
    password = request.form['password']
    new_user = User(name=name)
    new_user.set_password(password)
    new_user.insert(get_db())
    return redirect(url_for('manage_users'))

@app.route("/users/delete", methods=['POST'])
@requires_admin
def delete_user():
    User(id=int(request.form['id'])).delete(get_db())
    return redirect(url_for('manage_users'))

@app.route("/manage/add", methods=['POST'])
@login_required
def new_notification():
    channel_id = int(request.form['channel'])
    valid_from = datetime.strptime(request.form['valid_from'], date_fmt)
    valid_to = datetime.strptime(request.form['valid_to'], date_fmt)
    new_notification = Notification(channel=channel_id, summary=request.form['summary'],
                                    description=request.form['description'],
                                    valid_from=valid_from, valid_to=valid_to, location=request.form['location'])
    new_notification.insert(get_db())
    return redirect(url_for('list_notifications'))


@app.route("/manage/delete", methods=['POST'])
@login_required
def delete_notification():
    Notification(id=int(request.form['id'])).delete(get_db())
    return redirect(url_for('list_notifications'))


@app.route("/manage/delete_channel", methods=['POST'])
@login_required
def delete_channel():
    Channel(id=int(request.form['id'])).delete(get_db())
    return redirect(url_for('list_notifications'))


@app.route("/manage/add_channel", methods=['POST'])
@login_required
def new_channel():
    display_name = request.form['display_name']
    url = request.form['url']
    new_channel = Channel(display_name=display_name, url=url)
    new_channel.insert(get_db())
    return redirect(url_for('list_notifications'))


if __name__ == "__main__":
    app.run(host="0.0.0.0")
