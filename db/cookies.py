from ._base import BaseDb
import base64
import secrets


class CookieDb(BaseDb):
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

    def create_cookie(self, who: int, user_agent) -> str | None:
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
