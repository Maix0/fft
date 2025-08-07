from ._base import BaseDb


class NoteAccessDb(BaseDb):
    def get_note_access(self, userid: int):
        req = self.cur.execute("SELECT note_access FROM USERS WHERE id = ?", [userid])
        return req.fetchone()["note_access"]

    def set_note_access(self, userid: int, access: bool):
        req = self.cur.execute(
            "UPDATE USERS SET note_access = ? WHERE id = ?", [access, userid]
        )
        return req.fetchone()

    def get_all_note_access(self):
        req = self.cur.execute("SELECT * FROM USERS WHERE note_access == 1")
        return req.fetchall()
