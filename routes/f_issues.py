from globals import Db, config  # GLOBAL_IMPORT
from routes.helpers import (
    auth_required,
)
from flask import Blueprint

app = Blueprint("issues", __name__, template_folder="templates")


@app.route("/addissue/<pc>/<int:issue_type>")
@auth_required
def create_issue(pc, issue_type, userid):
    db = Db(config.db_path)
    success = db.create_issue(userid["userid"], pc, int(issue_type))
    db.close()
    if not success:
        return "", 400
    return "", 200


@app.route("/addissue/<token>/<pc>/<int:issue_type>")
def create_issue_bot(token, pc, issue_type):
    if token != config.update_key:
        return "Bad token", 400
    db = Db(config.db_path)
    success = db.create_issue(0, pc, int(issue_type))
    db.close()
    if not success:
        return "", 400
    return "", 200
