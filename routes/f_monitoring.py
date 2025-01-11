from globals import r, Db, api, config  # GLOBAL_IMPORT
import globals as gl
from routes.helpers import (
    time,
)
from flask import Blueprint

app = Blueprint("monitoring", __name__, template_folder="templates")


@app.route("/monitoring/<token>/api42")
def monitoring_api42(token):
    if token != gl.config.update_key:
        return "Bad token", 400
    return "", 200 if api.get_token() else 500


@app.route("/monitoring/<token>/db")
def monitoring_db(token):
    if token != gl.config.update_key:
        return "Bad token", 400
    try:
        db = Db(config.db_path)
        db.search("eee")
        db.close()
    except:
        return "BAD", 500
    return "OK", 200


@app.route("/monitoring/<token>/redis")
def monitoring_redis(token):
    if token != gl.config.update_key:
        return "Bad token", 400
    try:
        r.set("monitoring", time.time())
    except:
        return "BAD", 500
    return "OK", 200


@app.route("/monitoring/200")
def get_200():
    return "OK", 200
