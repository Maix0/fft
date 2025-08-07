from ._base import BaseDb


class CustomImageDb(BaseDb):
    def get_custom_image(self, userid: int):
        req = self.cur.execute(
            "SELECT custom_image_link FROM  USERS WHERE id = ?", [userid]
        )
        return req.fetchone()

    def set_custom_image(self, userid: int, link: str):
        req = self.cur.execute(
            "UPDATE USERS SET custom_image_link = ? WHERE id = ?", [link, userid]
        )
        return req.fetchall()

    def get_all_custom_images(self):
        req = self.cur.execute(
            "SELECT * FROM USERS WHERE custom_image_link IS NOT NULL"
        )
        return req.fetchall()
