from ._base import BaseDb


class PiscineDateDb(BaseDb):
    pass

    # Piscine dates
    def insert_piscine_date(self, month: str, year: str):
        self.cur.execute(
            "INSERT INTO PISCINE_DATES(month, year) VALUES(?, ?)", [month, year]
        )
        self.commit()

    def remove_piscine_date(self, piscine_date: int):
        self.cur.execute("DELETE FROM PISCINE_DATES WHERE id = ?", [piscine_date])
        self.commit()

    def get_all_piscine_dates(self):
        req = self.cur.execute("SELECT * FROM PISCINE_DATES")
        return req.fetchall()
