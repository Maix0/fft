from ._base import BaseDb


class UserDb(BaseDb):
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
        note = god("USERS", "note", uid)
        note_access = god("USERS", "note_access", uid)
        if not campus or type(campus) is not int:
            campus = 1
        self.cur.execute(
            "INSERT OR REPLACE INTO USERS(id, name, image, image_medium, pool, active, campus, tag, custom_image_link, note, note_access)"
            f"VALUES(?, ?, ?, ?, ?, {active}, {campus}, "
            f"(SELECT COALESCE({tag}, NULL)),"
            f"(SELECT COALESCE({custom_image_link}, NULL)),"
            f"(SELECT COALESCE({note}, NULL)),"
            f"(SELECT COALESCE({note_access}, NULL)))",
            [
                uid,
                user_data["login"],
                user_data["image"]["link"],
                user_data["image"]["versions"]["medium"],
                f"{user_data['pool_month']} {user_data['pool_year']}",
            ],
        )

    def get_all_notes(self) -> list:
        query = self.cur.execute("SELECT * FROM USERS WHERE note != ''")
        return query.fetchall()

    def get_user(self, login: str):
        query = self.cur.execute("SELECT id FROM USERS WHERE name = ?", [login])
        return query.fetchone()

    def get_user_by_id(self, user_id: int):
        query = self.cur.execute(
            "SELECT id, name, campus, image_medium FROM USERS WHERE id = ?", [user_id]
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
