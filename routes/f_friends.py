from globals import Db, api, config  # GLOBAL_IMPORT
from routes.helpers import (
    auth_required,
    create_users,
)
from flask import Blueprint

app = Blueprint("friends", __name__, template_folder="templates")


@app.route("/friends/add/<add>")
@auth_required
def add_friend(add, userid):
    db = Db(config.db_path)
    friends = add.split(",")
    failed_friends = []
    for friend in friends:
        friend = friend.strip().lower()
        if len(friend) < 3:
            failed_friends.append(friend)
            continue
        add_id = db.get_user(friend)
        if add_id is None:
            status, resp = api.get_unknown_user(friend)
            if status == 200:
                create_users(db, [{"user": resp}])
            else:
                val = db.get_user_profile(friend, api)
                if val:
                    resp = {"id": val["id"]}
                else:
                    failed_friends.append(friend)
                    continue
            add_id = {"id": resp["id"]}
        if not db.add_friend(userid["userid"], add_id["id"]):
            failed_friends.append(friend)
    db.close()
    if len(failed_friends):
        return f"failed_friends: {", ".join(failed_friends)}", 404
    return "Ok", 200


@app.route("/friends/remove/<remove>")
@auth_required
def remove_friend(remove, userid):
    db = Db(config.db_path)
    remove_id = db.get_user(remove)
    if remove_id is None:
        return "", 404
    success = db.remove_friend(userid["userid"], remove_id["id"])
    db.close()
    return "", 200 if success else 404


@app.route("/friends/set_relation/<who>/<int:relation>")
@auth_required
def set_relation(who, relation, userid):
    db = Db(config.db_path)
    who_id = db.get_user(who)
    if who_id is None:
        db.close()
        return "", 404
    success = db.set_relation(userid["userid"], who_id["id"], int(relation))
    db.close()
    return "", 200 if success else 500
