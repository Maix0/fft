from ._base import BaseDb


class AdminDb(BaseDb):
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
