from ._base import BaseDb


class WhitelistDb(BaseDb):
    def is_whitelisted(self, user_id: int) -> bool:
        query = self.cur.execute("SELECT 1 FROM WHITELIST WHERE user_id = ?", [user_id])
        return query.fetchone() is not None

    def add_whitelist(self, user_id: int, user_login: str):
        self.cur.execute(
            "INSERT INTO WHITELIST(user_id, user_login) VALUES(?, ?)",
            [user_id, user_login],
        )
        self.commit()

    def remove_whitelist(self, id: int):
        self.cur.execute("DELETE FROM WHITELIST WHERE id = ?", [id])
        self.commit()

    def get_all_whitelist(self) -> list:
        req = self.cur.execute("SELECT * FROM WHITELIST")
        return req.fetchall()
