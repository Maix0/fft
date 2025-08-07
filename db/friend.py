from ._base import BaseDb


class FriendDb(BaseDb):
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
