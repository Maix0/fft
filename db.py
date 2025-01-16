import sqlite3
import secrets
import base64
from routes.api_helpers import find_correct_campus
import config


def read_file(filename: str):
    with open(filename, "r") as f:
        return f.read()


def dict_factory(cursor, row) -> dict:
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Db:
    cur: sqlite3.Cursor = None
    con: sqlite3.Connection = None
    is_closed = False

    def __init__(self, filename=config.db_path):
        self.con = sqlite3.connect(filename)
        self.con.row_factory = dict_factory
        self.cur = self.con.cursor()

    # Management
    def initialize(self):
        self.create_table("scheme.sql")
        self.close()

    def commit(self):
        self.con.commit()

    def close(self):
        self.commit()
        self.con.close()
        self.is_closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.is_closed:
            self.close()

    def __del__(self):
        if not self.is_closed:
            self.close()

    def create_table(self, sql_file: str):
        self.cur.executescript(read_file(sql_file))

    # Tutors
    def set_tutors(self, values: list[tuple[int, str]]):
        self.cur.execute("DELETE FROM TUTORS")
        for id, name in values:
            # no Nimon, you are not a tutor :)
            if id == 60222:
                continue
            self.cur.execute("INSERT INTO TUTORS VALUES (?, ?)", [id, name])
        self.commit()

    def get_all_tutors(self):
        req = self.cur.execute(
            "SELECT USERS.* FROM TUTORS JOIN USERS ON USERS.id = TUTORS.id"
        )
        return req.fetchall()

    def is_tutors(self, userid: int):
        req = self.cur.execute("SELECT * FROM TUTORS where id = ?", [userid])
        return len(req.fetchall()) > 0

    # Users
    def create_user(self, user_data: dict, campus=1):
        def god(db, field, userid: int):
            """get old data"""
            return f"(SELECT {field} FROM {db} WHERE id = '{userid}')"

        uid = int(user_data["id"])
        active = (
            "CURRENT_TIMESTAMP"
            if user_data["location"]
            else god("USERS", "active", uid)
        )
        tag = god("USERS", "tag", uid)
        custom_image_link = god("USERS", "custom_image_link", uid)
        if not campus or type(campus) is not int:
            campus = 1
        self.cur.execute(
            "INSERT OR REPLACE INTO USERS(id, name, image, image_medium, pool, active, campus, tag, custom_image_link) "
            f"VALUES(?, ?, ?, ?, ?, {active}, {campus}, (SELECT COALESCE({tag}, NULL)),  (SELECT COALESCE({custom_image_link}, NULL)))",
            [
                uid,
                user_data["login"],
                user_data["image"]["link"],
                user_data["image"]["versions"]["medium"],
                f"{user_data['pool_month']} {user_data['pool_year']}",
            ],
        )

    def get_user(self, user_id: int):
        query = self.cur.execute("SELECT id FROM USERS WHERE name = ?", [user_id])
        return query.fetchone()

    def get_user_by_id(self, user_id: int):
        query = self.cur.execute(
            "SELECT name, campus, image_medium FROM USERS WHERE id = ?", [user_id]
        )
        return query.fetchone()

    def get_user_by_login(self, login: str):
        query = self.cur.execute(
            "SELECT id, name, campus, image_medium FROM USERS WHERE name = ?", [login]
        )
        return query.fetchone()

    def search(self, start: str):
        req = self.cur.execute(
            "SELECT name FROM USERS WHERE name LIKE ? LIMIT 5", [start + "%"]
        )
        resp = req.fetchall()
        return resp

    # Theme
    def update_theme(self, who: int, css: str, js: str, enabled: int):
        if who is None or enabled > 1 or enabled < 0:
            return False
        if len(css) > 5000 or len(js) > 5000:
            return False
        self.cur.execute(
            "INSERT OR REPLACE INTO THEME(userid, javascript, css, enabled) VALUES (?, ?, ?, ?)",
            [who, js, css, enabled],
        )
        self.commit()
        return True

    def get_theme(self, who):
        if who is None:
            return False
        query = self.cur.execute("SELECT * FROM THEME WHERE userid = ?", [who])
        data = query.fetchone()
        if data is None:
            return {"enabled": 0, "javascript": "", "css": ""}
        return data

    # Friends
    def add_friend(self, who: int, add_id: int):
        if who is None or add_id is None or add_id <= 0:
            return False
        self.cur.execute(
            "INSERT OR REPLACE INTO FRIENDS(who, has) VALUES (?, ?)", [who, add_id]
        )
        self.commit()
        return True

    def get_friends(self, who: int):
        query = self.cur.execute(
            "SELECT * FROM FRIENDS JOIN USERS ON USERS.id = FRIENDS.has WHERE who = ?",
            [who],
        )
        return query.fetchall()

    def get_notifications_friends(self, who: int):
        query = self.cur.execute(
            "SELECT * FROM FRIENDS JOIN USERS ON USERS.id = FRIENDS.has WHERE who = ? AND relation = 1",
            [who],
        )
        ret = query.fetchall()
        r_ret = []
        for friend in ret:
            tg = self.has_notifications(friend["has"])
            if tg and tg["enabled"] == 1 and self.is_friend(friend["has"], who) == 1:
                r_ret.append({"id": friend["has"], "tg": tg})
        return r_ret

    def is_friend(self, who: int, has: int) -> bool:
        req = self.cur.execute(
            "SELECT relation FROM FRIENDS WHERE who = ? AND has = ?", [who, has]
        )
        res = req.fetchone()
        if res is not None:
            return res["relation"]
        return False

    def remove_friend(self, who: int, remove: int):
        if who is None or remove is None or remove <= 0:
            return False
        self.cur.execute("DELETE FROM FRIENDS WHERE who = ? AND has = ?", [who, remove])
        self.con.commit()
        return True

    def set_relation(self, who: int, has: int, relation: int):
        if who is None or has is None or relation < 0 or relation > 1:
            return False
        self.cur.execute(
            "UPDATE FRIENDS SET relation = ? WHERE who = ? AND has = ?",
            [relation, who, has],
        )
        self.commit()
        return True

    # Cookies
    def get_user_by_bookie(self, cookie: str):
        req = self.cur.execute("SELECT userid FROM COOKIES WHERE uuid = ?", [cookie])
        ret = req.fetchone()
        if ret is None:
            return 0
        return ret

    def get_user_cookies(self, who: int) -> list:
        if who is None:
            return []
        req = self.cur.execute(
            "SELECT * FROM COOKIES WHERE userid = ? ORDER BY creation DESC LIMIT 25",
            [who],
        )
        ret = req.fetchall()
        if ret is None:
            return []
        return ret

    def get_user_all_cookies(self, who: int) -> list:
        if who is None:
            return []
        req = self.cur.execute(
            "SELECT * FROM COOKIES WHERE userid = ? ORDER BY creation DESC", [who]
        )
        ret = req.fetchall()
        if ret is None:
            return []
        return ret

    def reset_user_cookies(self, who: int):
        if who is None:
            return False
        self.cur.execute("DELETE FROM COOKIES WHERE userid = ?", [who])
        self.con.commit()
        return True

    def create_cookie(self, who: int, user_agent) -> str:
        while 1:
            token = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
            query = self.cur.execute("SELECT 1 FROM COOKIES WHERE uuid = ?", [token])
            ret = query.fetchone()
            if ret is not None:
                continue
            self.cur.execute(
                "INSERT INTO COOKIES(userid, uuid, name) VALUES(?, ?, ?)",
                [who, token, user_agent],
            )
            self.commit()
            return token

    def delete_cookie(self, cookie: str):
        self.cur.execute("DELETE FROM COOKIES WHERE uuid = ?", [cookie])

    # Dead PC
    def delete_issues(self, station: str):
        """
        Needs commit afterwards
        :param station: e1r1p1
        :return:
        """
        self.cur.execute("DELETE FROM DEAD_PC WHERE station = ?", [station])

    def already_created(self, who: int, station: str) -> bool:
        req = self.cur.execute(
            "SELECT 1 FROM DEAD_PC WHERE issuer = ? AND station = ?", [who, station]
        )
        res = req.fetchone()
        if res is None:
            return False
        return True

    def create_issue(self, who: int, station: str, issue: int) -> bool:
        if issue < 0 or issue > 5 or len(station) > 15 or len(station) < 6:
            return False
        if self.already_created(who, station):
            return False
        self.cur.execute(
            "INSERT INTO DEAD_PC(issuer, station, issue) VALUES(?, ?, ?)",
            [who, station, issue],
        )
        self.commit()
        return True

    def get_issues(self):
        req = self.cur.execute(
            "SELECT station, issue, since FROM DEAD_PC WHERE solved = 0"
        )
        return req.fetchall()

    def get_issues_by_user(self, user):
        req = self.cur.execute("SELECT * FROM DEAD_PC WHERE issuer = ?", [user])
        return req.fetchall()

    # Profile
    def set_profile(self, who: int, info: dict) -> bool:
        if (
            "description" not in info
            or "github" not in info
            or "discord" not in info
            or "website" not in info
        ):
            return False
        if (
            len(info["description"]) > 1500
            or len(info["discord"]) > 40
            or len(info["github"]) > 60
            or len(info["website"]) > 30
        ):
            return False
        if len(info["github"]) > 0 and not info["github"].startswith(
            "https://github.com/"
        ):
            return False
        if (
            (len(info["discord"]) > 50)
            or (len(info["github"]) > 0)
            and "https://github.com/" not in info["github"]
        ):
            return False
        if len(info["website"]) > 0 and not (
            info["website"].startswith("http://")
            or info["website"].startswith("https://")
        ):
            return False
        self.cur.execute(
            "INSERT OR REPLACE INTO PROFILES(userid, website, github, discord, recit) VALUES (?, ?, ?, ?, ?)",
            [
                who,
                info["website"],
                info["github"],
                info["discord"],
                info["description"],
            ],
        )
        self.commit()
        return True

    def get_user_profile(self, login, api=None):
        query = self.cur.execute(
            "SELECT * FROM USERS LEFT JOIN PROFILES ON PROFILES.userid = USERS.id WHERE name = ?",
            [str(login)],
        )
        ret = query.fetchone()
        if api and ret is None:
            ret_status, ret_data = api.get_unknown_user(login)
            if ret_status != 200:
                return None
            self.create_user(ret_data, find_correct_campus(ret_data))
            return self.get_user_profile(login)
        return ret

    def get_user_profile_id(self, login):
        """
        :param login: Login 42 id
        :return: SELECT * FROM USERS
        """
        query = self.cur.execute(
            "SELECT * FROM USERS LEFT JOIN PROFILES ON PROFILES.userid = USERS.id WHERE USERS.id = ?",
            [login],
        )
        return query.fetchone()

    def is_whitelisted(self, user_id: int) -> bool:
        query = self.cur.execute("SELECT 1 FROM WHITELIST WHERE user_id = ?", [user_id])
        return query.fetchone() is not None

    def add_whitelist(self, user_id: int, user_login: str) -> bool:
        self.cur.execute(
            "INSERT INTO WHITELIST(user_id, user_login) VALUES(?, ?)",
            [user_id, user_login],
        )
        self.commit()

    def remove_whitelist(self, id: int) -> bool:
        self.cur.execute("DELETE FROM WHITELIST WHERE id = ?", [id])
        self.commit()

    def get_all_whitelist(self) -> list:
        req = self.cur.execute("SELECT * FROM WHITELIST")
        return req.fetchall()

    # Update process
    def raw_query(self, query, args):
        return self.cur.execute(query, args)

    # Piscines
    def insert_piscine(self, campus: int, cluster: str):
        self.cur.execute(
            "INSERT INTO PISCINES(campus, cluster) VALUES(?, ?)", [campus, cluster]
        )
        self.commit()

    def remove_piscine(self, piscine: int):
        self.cur.execute("DELETE FROM PISCINES WHERE id = ?", [piscine])
        self.commit()

    def get_all_piscines(self):
        req = self.cur.execute("SELECT * FROM PISCINES")
        return req.fetchall()

    def get_piscines(self, campus: int):
        req = self.cur.execute("SELECT * FROM PISCINES WHERE campus = ?", [campus])
        return req.fetchall()

    def is_piscine(self, campus: int, cluster: str):
        req = self.cur.execute(
            "SELECT 1 FROM PISCINES WHERE campus = ? AND cluster LIKE ?",
            [campus, cluster],
        )
        return True if req.fetchone() else False

    # Piscine dates
    def insert_piscine_date(self, month: str, year: str):
        self.cur.execute(
            "INSERT INTO PISCINE_DATES(month, year) VALUES(?, ?)", [month, year]
        )
        self.commit()

    def remove_piscine_date(self, piscine_date: int):
        self.cur.execute("DELETE FROM PISCINE_DATES WHERE id = ?", [piscine_date])
        self.commit()

    def get_all_piscine_dates(self):
        req = self.cur.execute("SELECT * FROM PISCINE_DATES")
        return req.fetchall()

    # Silents clusters
    def insert_silent(self, campus: int, cluster: str):
        self.cur.execute(
            "INSERT INTO SILENTS(campus, cluster) VALUES(?, ?)", [campus, cluster]
        )
        self.commit()

    def remove_silent(self, silent: int):
        self.cur.execute("DELETE FROM SILENTS WHERE id = ?", [silent])
        self.commit()

    def get_all_silents(self):
        req = self.cur.execute("SELECT * FROM SILENTS")
        return req.fetchall()

    def get_silents(self, campus: int):
        req = self.cur.execute("SELECT * FROM SILENTS WHERE campus = ?", [campus])
        return req.fetchall()

    def is_silent(self, campus: int, cluster: str):
        req = self.cur.execute(
            "SELECT 1 FROM SILENTS WHERE campus = ? AND cluster LIKE ?",
            [campus, cluster],
        )
        return True if req.fetchone() else False

    # Tutor station clusters
    def insert_tutor_station(self, campus: int, station: str):
        self.cur.execute(
            "INSERT INTO TUTOR_STATION(campus, station) VALUES(?, ?)",
            [campus, station],
        )
        self.commit()

    def remove_tutor_station(self, tut_id: int):
        self.cur.execute("DELETE FROM TUTOR_STATION WHERE id = ?", [tut_id])
        self.commit()

    def get_all_tutor_stations(self):
        req = self.cur.execute("SELECT * FROM TUTOR_STATION")
        return req.fetchall()

    def get_tutor_stations(self, campus: int):
        req = self.cur.execute("SELECT * FROM TUTOR_STATION WHERE campus = ?", [campus])
        return req.fetchall()

    def is_tutor_station(self, campus: int, station: str):
        req = self.cur.execute(
            "SELECT 1 FROM TUTOR_STATION WHERE campus = ? AND station = ?",
            [campus, station],
        )
        return True if req.fetchone() else False

    def get_user_tag(self, user_id: int):
        req = self.cur.execute("SELECT tag FROM USERS WHERE id = ?", [user_id])
        return req.fetchone()

    def set_user_tag(self, user_id: int, tag: str):
        req = self.cur.execute("UPDATE USERS SET tag= ? WHERE id = ?", [tag, user_id])
        return req.fetchall()

    def get_all_user_tags(self):
        req = self.cur.execute(
            "SELECT id, name, tag FROM USERS WHERE tag IS NOT NULL", []
        )
        return req.fetchall()

    # Admin
    def is_admin(self, user_id: int):
        req = self.cur.execute("SELECT * FROM PERMISSIONS WHERE user_id = ?", [user_id])
        res = req.fetchone()
        if res is None:
            return False
        return res

    def get_admin_tag(self, user_id: int):
        req = self.cur.execute(
            "SELECT tag FROM PERMISSIONS WHERE user_id = ?", [user_id]
        )
        return req.fetchall()

    def admin_change_tag(self, user_id: int, tag: str):
        self.cur.execute(
            "UPDATE PERMISSIONS SET tag = ? WHERE user_id = ?", [tag, user_id]
        )
        self.commit()

    def get_all_admins(self):
        req = self.cur.execute("SELECT * FROM PERMISSIONS")
        return req.fetchall()
    
    #
    # CUSTOM IMAGE 
    #

    def get_custom_image(self, userid: int):
        req = self.cur.execute("SELECT custom_image_link FROM  USERS WHERE id = ?", [userid])
        return req.fetchone()

    def set_custom_image(self, userid: int, link: str):
        req = self.cur.execute("UPDATE USERS SET custom_image_link = ? WHERE id = ?", [link, userid])
        return req.fetchall()

    def get_all_custom_images(self):
        req = self.cur.execute("SELECT * FROM USERS WHERE custom_image_link IS NOT NULL")
        return req.fetchall()
