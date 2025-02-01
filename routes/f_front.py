from globals import Db, api, config  # GLOBAL_IMPORT
from routes.helpers import (
    arrow,
    auth_required,
    get_cached_locations,
    get_position,
    request,
    standard_cluster,
)
from flask import (
    Blueprint,
    render_template,
    send_from_directory,
)
import maps.maps as maps

app = Blueprint("front", __name__, template_folder="templates", static_folder="static")


@app.route("/profile/<login>")
@auth_required
def profile(login, userid):
    with Db() as db:
        user = db.get_user_profile(login, api)
        if user is None:
            return "", 404
        is_friend = db.is_friend(userid["userid"], user["id"]) is not False
        theme = db.get_theme(userid["userid"])
        tag = db.get_admin_tag(user_id=user["id"])
        if len(tag):
            user.update({"admintag": db.get_admin_tag(user_id=user["id"])[0]["tag"]})
        else:
            user.update({"admintag": ""})
        if user["tag"] is None:
            user["tag"] = ""
    if user is None:
        return "", 404
    user["position"] = get_position(user["name"])
    if user["active"] and user["position"] is None:
        user["last_active"] = "depuis " + (
            arrow.get(user["active"], "YYYY-MM-DD HH:mm:ss", tzinfo="UTC")
        ).humanize(locale="FR", only_distance=True)
    else:
        user["last_active"] = ""
    if user["note"] is None:
        user["note"] = ""
    #if userid["is_tutor"]:
    #    user["note"] = user["note"].replace("\n", "<br>")
    return render_template(
        "profile.html",
        user=user,
        is_friend=is_friend,
        userid=userid,
        theme=theme,
    )


@app.route("/import_friends/", methods=["GET"])
@app.route("/import_friends", methods=["GET"])
@auth_required
def import_friends(userid):
    return render_template("import_friends.html")


@app.route("/settings/", methods=["GET", "POST"])
@auth_required
def settings(userid):
    db = Db(config.db_path)
    login = db.get_user_by_id(userid["userid"])["name"]
    user = db.get_user_profile(login)
    theme = db.get_theme(userid["userid"])
    cookies = db.get_user_cookies(userid["userid"])
    campus_id = db.get_user_by_id(userid["userid"])["campus"]
    db.close()
    kiosk_buildings = {}
    if campus_id in maps.available:
        kiosk_buildings = maps.available[campus_id].map["buildings"]
    return render_template(
        "settings.html",
        user=user,
        theme=theme,
        cookies=cookies,
        kiosk_buildings=kiosk_buildings,
        domain=config.domain,
    )


@app.route("/")
@auth_required
def index(userid):
    pos = standard_cluster(get_position(userid["userid"]))
    db = Db(config.db_path)
    campus_id = db.get_user_by_id(userid["userid"])["campus"]
    if campus_id not in maps.available:
        db.close()
        return render_template("campus_refresh.html", campus_id=campus_id)
    friends = db.get_friends(userid["userid"])
    issues = db.get_issues()
    admins = db.get_all_admins()
    whitelists = db.get_all_whitelist()
    admin_ids = set()
    whitelist_ids = set()
    for admin in admins:
        admin_ids.add(admin["user_id"])
    for user in whitelists:
        whitelist_ids.add(user["user_id"])
    me = db.get_user_profile_id(userid["userid"])
    theme = db.get_theme(userid["userid"])
    tutors = [x["id"] for x in db.get_all_tutors()]
    piscines = [x["cluster"] for x in db.get_piscines(userid["campus"])]
    silents = [x["cluster"] for x in db.get_silents(userid["campus"])]
    piscine_date = [(x["month"], x["year"]) for x in db.get_all_piscine_dates()]
    custom_images = {
        x["name"]: x["custom_image_link"] for x in db.get_all_custom_images()
    }

    tutor_stations = [
        x["station"]
        for x in db.get_all_tutor_stations()
        if x["campus"] == userid["campus"]
    ]
    db.close()
    campus_map = maps.available[campus_id].map
    if pos and campus_map["exrypz"](pos) is bool:
        pos = campus_map["default"]
    else:
        pos = campus_map["default"] if not pos else campus_map["exrypz"](pos)["etage"]
    cache_tab = get_cached_locations(campus_id)
    cluster_name = (
        pos if request.args.get("cluster") is None else request.args.get("cluster")
    )
    if cluster_name not in campus_map["allowed"]:
        cluster_name = campus_map["default"]
    location_map = {}
    issues_map = {}
    # TODO: optimize this
    for user in cache_tab:
        user_id = user["user"]["id"]
        friend, close_friend = False, False
        friend = user_id in [e["has"] for e in friends]
        if friend:
            close_friend = user_id in [e["has"] for e in friends if e["relation"] == 1]
        admin = user_id in admin_ids
        whitelist = user_id in whitelist_ids
        if user["user"]["login"] in custom_images:
            user["user"]["image"]["versions"]["small"] = custom_images[
                user["user"]["login"]
            ]
        location_map[user["host"]] = {
            **user,
            "me": user_id == userid["userid"],
            "friend": friend,
            "close_friend": close_friend,
            "admin": admin,
            "whitelist": whitelist,
            "pool": False,
        }
        if me and "pool" in me:
            location_map[user["host"]]["pool"] = (
                f"{user['user']['pool_month']} {user['user']['pool_year']}"
                == me["pool"]
            )
    for issue in issues:
        if issue["station"] not in issues_map:
            issues_map[issue["station"]] = {"count": 0}
        issues_map[issue["station"]]["issue"] = issue["issue"]
        issues_map[issue["station"]]["count"] += 1
    clusters_list = [
        {
            "name": cluster,
            "exrypz": campus_map["exrypz"],
            "map": campus_map[cluster],
            "maximum_places": maps.places(campus_map["exrypz"], campus_map[cluster]),
            "users": maps.count_in_cluster(cluster, location_map),
            "dead_pc": maps.count_in_cluster(cluster, issues_map),
            "places": maps.available_seats(
                cluster,
                campus_map[cluster],
                campus_map["exrypz"],
                location_map,
                issues_map,
            ),
        }
        for cluster in campus_map["allowed"]
    ]
    return render_template(
        "index.html",
        map=campus_map[cluster_name],
        locations=location_map,
        clusters=clusters_list,
        actual_cluster=cluster_name,
        issues_map=issues_map,
        exrypz=campus_map["exrypz"],
        piscine=piscines,
        theme=theme,
        silent=silents,
        focus=request.args.get("p"),
        tutor_station=tutor_stations,
        piscine_date=piscine_date,
        tutors=tutors,
    )


@app.route("/friends/")
@auth_required
def friends_route(userid):
    db = Db(config.db_path)
    theme = db.get_theme(userid["userid"])
    friend_list = db.get_friends(userid["userid"])
    for friend in friend_list:
        friend.update({"admin": {"tag": db.get_admin_tag(friend["id"])}})
        if len(friend["admin"]["tag"]) == 0:
            friend["admin"]["tag"] = ""
        else:
            friend["admin"]["tag"] = friend["admin"]["tag"][0]["tag"]
        friend["position"] = get_position(friend["name"])
        if friend["tag"] is None:
            friend["tag"] = ""
        if friend["active"] and friend["position"] is None:
            date = arrow.get(friend["active"], "YYYY-MM-DD HH:mm:ss", tzinfo="UTC")
            friend["last_active"] = "depuis " + date.humanize(
                locale="FR", only_distance=True
            )
        else:
            friend["last_active"] = ""
    friend_list = sorted(friend_list, key=lambda d: d["name"])
    friend_list = sorted(friend_list, key=lambda d: 0 if d["relation"] == 1 else 1)
    friend_list = sorted(friend_list, key=lambda d: 0 if d["position"] else 1)
    db.close()
    return render_template("friends.html", friends=friend_list, theme=theme, add=True)


@app.route("/profile/tutors/setnote", methods=["POST"])
@auth_required
def add_whilelist(userid):
    if not userid["is_tutor"]:
        return "Not authorized", 401
    with Db() as db:
        user_id = int(request.form["user_id"].strip().lower())
        if user_id == 0:
            return "Login does not exist", 404
        db.set_note(user_id=user_id, note=request.form["note"])
    return ""


@app.route("/tutors/")
@auth_required
def tutors_route(userid):
    db = Db(config.db_path)
    theme = db.get_theme(userid["userid"])
    tutor_list = db.get_all_tutors()
    for tutor in tutor_list:
        tutor.update({"has": 0})
        tutor.update({"admin": {"tag": db.get_admin_tag(tutor["id"])}})
        if len(tutor["admin"]["tag"]) == 0:
            tutor["admin"]["tag"] = ""
        else:
            tutor["admin"]["tag"] = tutor["admin"]["tag"][0]["tag"]
        tutor["position"] = get_position(tutor["name"])
        if tutor["tag"] is None:
            tutor["tag"] = ""
        if tutor["active"] and tutor["position"] is None:
            date = arrow.get(tutor["active"], "YYYY-MM-DD HH:mm:ss", tzinfo="UTC")
            tutor["last_active"] = "depuis " + date.humanize(
                locale="FR", only_distance=True
            )
        else:
            tutor["last_active"] = ""
    tutor_list = sorted(tutor_list, key=lambda d: d["name"])
    tutor_list = sorted(tutor_list, key=lambda d: 0 if d["position"] else 1)
    db.close()
    return render_template("friends.html", friends=tutor_list, theme=theme, add=False)


@app.route("/search/<keyword>/<int:friends_only>")
@auth_required
def search_route(keyword, friends_only, userid):
    if len(keyword) < 2 or "%" in keyword:
        return "", 400
    if "," in keyword:
        keyword = keyword.split(",")[-1].strip()
        if len(keyword) < 3:
            return "", 400
    keyword = keyword.lower()
    db = Db(config.db_path)
    req_friends = db.search(keyword)
    db.close()
    resp = [{"type": "user", "v": e["name"], "s": e["name"]} for e in req_friends]
    return resp, 200


# Manual things that need to be routed on /


@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "img/favicon.ico")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/service_worker.json")
def service_worker():
    return send_from_directory("static", "js/service_worker.js")


@app.route("/apple-touch-icon.png")
def apple_touch_icon():
    return send_from_directory("static", "img/apple-touch-icon.png")
