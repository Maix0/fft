from ._base import BaseDb


class ThemeDb(BaseDb):
    pass

    # Theme
    def update_theme(self, who: int, css: str, js: str, enabled: int):
        if who is None or enabled > 1 or enabled < 0:
            return False
        if len(css) > 5000 or len(js) > 5000:
            return False
        self.cur.execute(
            "INSERT OR REPLACE INTO THEME(userid, javascript, css, enabled) VALUES (?, ?, ?, ?)",
            [who, js, css, enabled],
        )
        self.commit()
        return True

    def get_theme(self, who):
        if who is None:
            return False
        query = self.cur.execute("SELECT * FROM THEME WHERE userid = ?", [who])
        data = query.fetchone()
        if data is None:
            return {"enabled": 0, "javascript": "", "css": ""}
        return data
