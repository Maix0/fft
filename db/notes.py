from ._base import BaseDb


class NoteDb(BaseDb):
    def set_note(self, user_id: int, note: str):
        req = self.cur.execute(
            "UPDATE USERS SET note = ? WHERE id = ?", [note, user_id]
        )
        res = req.fetchone()
        if res is None:
            return False
        return res
