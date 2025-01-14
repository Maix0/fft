from globals import Db, api, config  # GLOBAL_IMPORT
from routes.helpers import (
    auth_required,
    request,
    verify_csrf,
)
from flask import (
    Blueprint,
    render_template,
    redirect,
)

app = Blueprint("admin", __name__, template_folder="templates", static_folder="static")


@app.route("/admin")
@auth_required
def admin(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    with Db() as db:
        piscines = db.get_all_piscines()
        silents = db.get_all_silents()
        whitelist = db.get_all_whitelist()
        admin = db.get_all_admins()
        tags = db.get_all_tags()
        tutor_station = db.get_all_tutor_stations()
        piscines_dates = db.get_all_piscine_dates()
    return render_template(
        "admin.html",
        user=userid,
        piscines=piscines,
        silents=silents,
        whitelist=whitelist,
        admins=admin,
        tutor_stations=tutor_station,
        tags=tags,
        piscines_dates=piscines_dates,
    )


@app.route("/admin/")
@auth_required
def admin_redirect(userid):
    return redirect("/admin", 307)


@app.route("/admin/update/tutors/<token>")
def update_tutors(token):
    if token != config.update_key:
        return "Bad token", 400
    # 166 is the id of the badge Tutors
    tutors = api.get_all_in_group(166)
    if tutors == 0:
        return "Error", 500
    with Db() as db:
        for tut in tutors:
            db.get_user_profile(tut["login"], api)
        db.set_tutors([(tut["id"], tut["login"]) for tut in tutors])
    return "OK", 200


@app.route("/admin/update/user/<login>")
@auth_required
def update_user(login, userid):
    if not userid["admin"]:
        return "Not authorized", 401
    # 166 is the id of the badge Tutors
    with Db() as db:
        ret = db.get_user_profile(login, api)
    return ("OK", 200) if ret else ("Error", 503)


##
## WHITELIST
##


@app.route("/admin/add/whitelist", methods=["POST"])
@auth_required
def add_whilelist(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(request.form["csrf"]):
        return "Please refresh and try again", 401
    with Db() as db:
        login = request.form["login"].strip().lower()
        user_id = api.get_user_id_by_login(login)
        db.get_user_profile(login, api)
        if user_id == 0:
            return "Login does not exist", 404
        db.add_whitelist(user_id=user_id, user_login=login)
    return ""


@app.route("/admin/remove/whitelist/<int:ban_id>/<csrf>")
@auth_required
def remove_whitelist(ban_id, csrf, userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(csrf):
        return "Please refresh and try again", 401
    with Db() as db:
        db.remove_whitelist(int(ban_id))
    return ""


##
## TUTOR STATION
##


@app.route("/admin/add/tutor_station", methods=["POST"])
@auth_required
def add_tutor_station(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(request.form["csrf"]):
        return "Please refresh and try again", 401
    with Db() as db:
        station = request.form["station"].strip()
        campus = int(request.form["campus"])
        db.insert_tutor_station(campus=campus, station=station)
    return ""


@app.route("/admin/remove/tutor_station/<int:ban_id>/<csrf>")
@auth_required
def remove_tutor_station(ban_id, csrf, userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(csrf):
        return "Please refresh and try again", 401
    with Db() as db:
        db.remove_tutor_station(int(ban_id))
    return ""


##
## TAGS (USER / ADMIN)
##


@app.route("/admin/set/user_tag", methods=["POST"])
@auth_required
def set_user_tag(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(request.form["csrf"]):
        return "Please refresh and try again", 401
    with Db() as db:
        login = request.form["login"].strip().lower()
        user = db.get_user_profile(login, api)
        tag = request.form["tag"].strip()
        if tag == "":
            db.set_tag(user_id=user["id"], tag=None)
        else:
            db.set_tag(user_id=user["id"], tag=tag)
    return ""


@app.route("/admin/set/admin_tag", methods=["POST"])
@auth_required
def set_admin_tag(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(request.form["csrf"]):
        return "Please refresh and try again", 401
    user_to_change = (
        request.form["user_id"]
        if request.form.get("user_id", None)
        else userid["userid"]
    )
    with Db() as db:
        db.admin_change_tag(user_to_change, request.form["tag"].strip())
    return ""


##
## PISCINE
##


@app.route("/admin/add/piscine", methods=["POST"])
@auth_required
def add_piscine(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(request.form["csrf"]):
        return "Please refresh and try again", 401
    with Db() as db:
        db.insert_piscine(int(request.form["campus"]), request.form["cluster"].strip())
    return ""


@app.route("/admin/remove/piscine/<int:ban_id>/<csrf>")
@auth_required
def remove_piscine(ban_id, csrf, userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(csrf):
        return "Please refresh and try again", 401
    with Db() as db:
        db.remove_piscine(int(ban_id))
    return ""


##
## SILENT
##


@app.route("/admin/add/silent", methods=["POST"])
@auth_required
def add_silent(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(request.form["csrf"]):
        return "Please refresh and try again", 401
    with Db() as db:
        db.insert_silent(int(request.form["campus"]), request.form["cluster"].strip())
    return ""


@app.route("/admin/remove/silent/<int:ban_id>/<csrf>")
@auth_required
def remove_silent(ban_id, csrf, userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(csrf):
        return "Please refresh and try again", 401
    with Db() as db:
        db.remove_silent(int(ban_id))
    return ""


##
## PISCINE DATES
##


@app.route("/admin/add/piscine_date", methods=["POST"])
@auth_required
def add_piscine_date(userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(request.form["csrf"]):
        return "Please refresh and try again", 401
    with Db() as db:
        db.insert_piscine_date(
            request.form["month"].strip().lower(), request.form["year"].strip().lower()
        )
    return ""


@app.route("/admin/remove/piscine_date/<int:ban_id>/<csrf>")
@auth_required
def remove_piscine_date(ban_id, csrf, userid):
    if not userid["admin"]:
        return "Not authorized", 401
    if not verify_csrf(csrf):
        return "Please refresh and try again", 401
    with Db() as db:
        db.remove_piscine_date(int(ban_id))
    return ""
