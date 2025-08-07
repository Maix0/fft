from ._base import BaseDb


class SilentDb(BaseDb):
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
