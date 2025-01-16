from globals import r, Db, api, config  # GLOBAL_IMPORT
from functools import wraps
from flask import request, redirect, make_response, g
import json
import hashlib
import hmac
import time
import secrets
import datetime
import arrow
import zlib
from routes.api_helpers import find_correct_campus


def proxy_images(url: str, light=False):
    if not url:
        return "/static/img/unknown.jpg"
    if light:
        return url.replace("https://cdn.intra.42.fr/", f"https://${config.proxy_domain}/proxy/70x70/")
    if "small" in url or "medium" in url:
        return url.replace("https://cdn.intra.42.fr/", f"https://${config.proxy_domain}/proxy/256x256/")
    return url.replace("https://cdn.intra.42.fr/", f"https://${config.proxy_domain}/proxy/512x512/")


def auth_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("token")
        db = Db(config.db_path)
        userid = db.get_user_by_bookie(token)
        if userid == 0:
            db.close()
            resp = make_response(redirect("/redirect_42", 307))
            resp.set_cookie(
                "previous",
                str(request.url_rule),
                secure=True,
                max_age=None,
                httponly=True,
            )
            return resp
        is_admin = db.is_admin(userid["userid"])
        if (not db.is_whitelisted(userid["userid"])) and (not is_admin):
            return "You are not whitelist from this website.", 403
        details = db.get_user_by_id(userid["userid"])
        theme = db.get_theme(userid["userid"])
        tag = db.get_user_tag(userid["userid"])
        is_tutor = db.is_tutors(userid["userid"])
        db.close()
        userid["admin"] = is_admin
        userid["tag"] = tag["tag"]
        userid["campus"] = details["campus"]
        userid["login"] = details["name"]
        userid["image_medium"] = proxy_images(details["image_medium"])
        userid["theme"] = theme
        userid["is_tutor"] = is_tutor
        g.user = userid
        kwargs["userid"] = userid
        return function(*args, **kwargs)

    return wrapper


def gen_session():
    return secrets.token_urlsafe(30)


def create_hooks(app):
    @app.before_request
    def hook_session():
        if "session" not in request.cookies:
            g.session = gen_session()
            g.set_session_cookie = True
        else:
            g.session = request.cookies["session"]

    @app.after_request
    def after_request(response):
        if "set_session_cookie" in g:
            response.set_cookie("session", g.session, None)
        return response


def create_csrf():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    random = secrets.token_urlsafe(20)
    msg = timestamp + "," + random + ""
    signature = hmac.new(
        (config.secret + g.session).encode("ascii"),
        msg=msg.encode("ascii"),
        digestmod=hashlib.sha256,
    )
    return msg + ":" + signature.hexdigest()


def verify_csrf(csrf: str):
    if ":" not in csrf and "," not in csrf:
        return False
    msg = csrf.split(":")[0]
    signature = csrf.split(":")[1]
    try:
        date = time.strptime(csrf.split(",")[0], "%Y-%m-%d-%H-%M-%S")
    except ValueError:
        return False
    if (time.time() - time.mktime(date)) > 1500:
        return False
    digest = hmac.new(
        (config.secret + g.session).encode("ascii"),
        msg=msg.encode("ascii"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


def get_position(name):
    ret = r.get("USER>" + str(name))
    return ret.decode("utf-8") if ret is not None else None


def standard_cluster(pos):
    if pos and "paul" in pos:
        pos = pos.replace("A", "")
        pos = pos.replace("B", "")
    return pos


def create_users(db, profiles):
    for elem in profiles:
        campus = find_correct_campus(elem)
        db.create_user(elem["user"], campus)
        if elem["user"]["location"]:
            db.delete_issues(elem["user"]["location"])
            r.set("USER>" + str(elem["user"]["id"]), elem["user"]["location"], ex=200)
            r.set(
                "USER>" + str(elem["user"]["login"]), elem["user"]["location"], ex=200
            )
            r.set("PERM>" + str(elem["user"]["login"]), elem["user"]["location"])
    db.commit()


def get_last_pos(login):
    x = r.get("PERM>" + login)
    if not x:
        return "Unknown"
    return x.decode("utf-8")


def get_cached_locations(campus=1):
    locations = r.get("locations/" + str(campus)) or "[]"
    # locations[0] == '[':
    if locations[0] == 91 or locations[0] == "[":
        cache_tab = json.loads(locations)
    else:
        cache_tab = json.loads(zlib.decompress(locations).decode("utf-8"))
    return cache_tab


def get_last_update(campus=1):
    last_update = r.get("location_last_update/" + str(campus))
    success = r.get("location_success/" + str(campus))
    if last_update:
        return arrow.get(last_update.decode("utf-8")), success.decode("utf-8") == "1"
    return None, False


def optimize_locations(data: list[dict]) -> list[dict]:
    if len(data) == 0:
        return data
    compressed = []
    for user in data:
        tmp = user["user"]
        user["host"] = user["host"].replace("made-f0b", "made-f0B")
        user["host"] = user["host"].replace("made-f0c", "made-f0C")
        compressed.append(
            {
                "id": user["id"],
                "host": user["host"],
                "campus_id": user["campus_id"],
                "user": {
                    "id": tmp["id"],
                    "login": tmp["login"],
                    "pool_month": tmp["pool_month"],
                    "pool_year": tmp["pool_year"],
                    "location": tmp["location"],
                    "image": {
                        "link": tmp["image"]["link"],
                        "versions": {
                            "medium": tmp["image"]["versions"]["medium"],
                            "small": tmp["image"]["versions"]["small"],
                        },
                    },
                },
            }
        )
    return compressed


def locs(campus=1):
    status, data = api.get_paged_locations(campus)
    if status == 200:
        data = optimize_locations(data)
        with Db(config.db_path) as db:
            create_users(db, data)
        r.set(
            "locations/" + str(campus), zlib.compress(json.dumps(data).encode("utf-8"))
        )
        r.set("location_last_update/" + str(campus), arrow.now().__str__())
        r.set("location_success/" + str(campus), "1")
        return data, 200
    else:
        r.set("location_success/" + str(campus), "0")
        return data, status


def date_fmt_locale(date: str, fmt="DD/MM/YYYY HH:mm:ss"):
    if date is None:
        return arrow.now().to("local").format(fmt, locale="fr")
    if type(date) is not str:
        return "?"
    return arrow.get(date).to("local").format(fmt, locale="fr")


def date_relative(date, granularity=None):
    if granularity:
        return arrow.get(date).humanize(locale="fr", granularity=granularity)
    return arrow.get(date).humanize(locale="fr")


def get_cached_user_data(user):
    data = r.get(f"data>{user}")
    if data == "":
        return None
    if data:
        return json.loads(data)
    status, data = api.get_unknown_user(user)
    if status != 200:
        r.set("data>user", "", ex=2)
        return None
    data["refreshed"] = arrow.now().__str__()
    r.set(f"data>{user}", json.dumps(data), ex=43200)
    return data


def get_cursus(data, cursus_name):
    if data is None:
        return None
    for cursus in data["cursus_users"]:
        if cursus["cursus"]["name"] == cursus_name:
            return cursus
    return None
