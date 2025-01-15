from globals import Db, api, config  # GLOBAL_IMPORT
from routes.helpers import (
    auth_required,
    get_position,
    proxy_images,
    redirect,
    request,
)
from flask import Blueprint

app = Blueprint("users", __name__, template_folder="templates")


@app.route("/getuser/<login>")
@auth_required
def getuser(login, userid):
    with Db() as db:
        user = db.get_user_profile(login, api)
        if user is None:
            return "", 404
        is_friend = db.is_friend(userid["userid"], user["id"])
        user["admin"] = db.is_admin(user["id"])
    user["is_friend"] = is_friend
    user["position"] = get_position(user["name"])
    user["image"] = proxy_images(user["image"])
    return dict(user)


@app.route("/settings/profile", methods=["POST"])
@auth_required
def settings_profile(userid):
    info = request.json
    if info is None:
        return 400
    db = Db(config.db_path)
    success = db.set_profile(userid["userid"], dict(info))
    db.close()
    if not success:
        return "", 400
    return redirect("/settings/", 307)
