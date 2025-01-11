from globals import Db, config  # GLOBAL_IMPORT
import globals as gl
from routes.helpers import (
    auth_required,
    request,
)
from flask import Blueprint

app = Blueprint("theme", __name__, template_folder="templates")


@app.route("/theme/set/", methods=["POST"])
@auth_required
def theme_set(userid):
    data = request.get_json()
    if not data:
        return "", 401
    if "javascript" not in data or "css" not in data or "enabled" not in data:
        return "", 402
    db = Db(config.db_path)
    ret = db.update_theme(
        userid["userid"], data["css"], data["javascript"], int(data["enabled"])
    )
    db.close()
    if ret:
        return "", 200
    else:
        return "", 400


@app.route("/reset")
@auth_required
def theme_disable(userid):
    db = Db(gl.config.db_path)
    data = db.get_theme(userid["userid"])
    ret = db.update_theme(userid["userid"], data["css"], data["javascript"], 0)
    db.close()
    if ret:
        return "OK", 200
    return "Erreur!!!", 400
