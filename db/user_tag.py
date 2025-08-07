from ._base import BaseDb


class UserTagDb(BaseDb):
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
