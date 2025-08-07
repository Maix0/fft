from ._base import BaseDb


class TutorDb(BaseDb):
    # Tutors
    def set_tutors(self, values: list[tuple[int, str]]):
        self.cur.execute("DELETE FROM TUTORS")
        for id, name in values:
            # no Nimon, you are not a tutor :)
            if id == 60222:
                continue
            self.cur.execute("INSERT INTO TUTORS VALUES (?, ?)", [id, name])
        self.commit()

    def get_all_tutors(self):
        req = self.cur.execute(
            "SELECT USERS.* FROM TUTORS JOIN USERS ON USERS.id = TUTORS.id"
        )
        return req.fetchall()

    def is_tutors(self, userid: int):
        req = self.cur.execute("SELECT * FROM TUTORS where id = ?", [userid])
        return len(req.fetchall()) > 0
