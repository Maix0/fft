from ._base import BaseDb


class TutorStationDb(BaseDb):
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
