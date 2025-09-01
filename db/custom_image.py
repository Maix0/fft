from ._base import BaseDb


class CustomImageDb(BaseDb):
    def get_custom_image(self, who: int):
        return self.cur.execute("SELECT * FROM IMAGES WHERE id = ?", [who]).fetchone()

    def set_custom_image(self, who: int, by: int):
        return self.cur.execute(
            "INSERT OR REPLACE INTO IMAGES(id, by, at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            [who, by],
        ).fetchone()
    
    def remove_custom_image(self, who: int):
        return self.cur.execute(
            "DELETE FROM IMAGES WHERE id = ?",
            [who],
        ).fetchone()

    def get_all_custom_images(self):
        req = self.cur.execute("SELECT * FROM IMAGES")
        return req.fetchall()

    def get_all_custom_images_pretty(self):
        req = self.cur.execute(
            """
select IMAGES.id as "id", U_WHO.name as "who", U_BY.name as "by", IMAGES.at from IMAGES
    left join USERS U_WHO on U_WHO.id = IMAGES."id"
    left join USERS U_BY on U_BY.id = IMAGES."by"
        """
        )
        return req.fetchall()
