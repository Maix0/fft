from ._base import BaseDb


class DeadPcDb(BaseDb):
    pass

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
        station = station.replace("f1b", "F1B")
        station = station.replace("f", "F")
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
