from globals import Db  # GLOBAL_IMPORT
import globals as gl
from routes.helpers import (
    auth_required,
)
from flask import Blueprint

app = Blueprint("session", __name__, template_folder="templates")


@app.route("/sessions/reset/")
@auth_required
def session_reset(userid):
    db = Db(gl.config.db_path)
    db.reset_user_cookies(userid["userid"])
    db.close()
    return "", 200
