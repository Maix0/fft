from globals import Db, api, config  # GLOBAL_IMPORT
from routes.helpers import (
    auth_required,
    create_users,
)
from flask import Blueprint

app = Blueprint("links", __name__, template_folder="templates")


@app.route("/links/add/<add>/<int:relation>")
@auth_required
def add_link(add: str, userid, relation: int):
    db = Db(config.db_path)
    links = add.split(",")
    failed_links = []
    for link in links:
        link = link.strip().lower()
        if len(link) < 3:
            failed_links.append(link)
            continue
        add_id = db.get_user(link)
        if add_id is None:
            status, resp = api.get_unknown_user(link)
            if status == 200:
                create_users(db, [{"user": resp}])
            else:
                val = db.get_user_profile(link, api)
                if val:
                    resp = {"id": val["id"]}
                else:
                    failed_links.append(link)
                    continue
            add_id = {"id": resp["id"]}
        if not db.add_link(userid["userid"], add_id["id"], relation=relation):
            failed_links.append(link)
    db.close()
    if len(failed_links):
        return f"failed_links: {', '.join(failed_links)}", 404
    return "Ok", 200


@app.route("/links/remove/<remove>")
@auth_required
def remove_link(remove: str, userid):
    db = Db(config.db_path)
    remove_id = db.get_user(remove)
    if remove_id is None:
        return "", 404
    success = db.remove_link(userid["userid"], remove_id["id"])
    db.close()
    return "", 200 if success else 404


@app.route("/links/set_relation/<who>/<int:relation>")
@auth_required
def set_relation(who: str, relation: int, userid):
    db = Db(config.db_path)
    who_id = db.get_user(who)
    if who_id is None:
        db.close()
        return "", 404
    success = db.set_link_relation(userid["userid"], who_id["id"], relation)
    db.close()
    return "", 200 if success else 500
