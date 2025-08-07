from ._base import BaseDb


class PiscineDb(BaseDb):
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
