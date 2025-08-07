from .user import UserDb

from routes.api_helpers import find_correct_campus


class ProfileDb(UserDb):
    # Profile
    def set_profile(self, who: int, info: dict) -> bool:
        if (
            "description" not in info
            or "github" not in info
            or "discord" not in info
            or "website" not in info
        ):
            return False
        if (
            len(info["description"]) > 1500
            or len(info["discord"]) > 40
            or len(info["github"]) > 60
            or len(info["website"]) > 30
        ):
            return False
        if len(info["github"]) > 0 and not info["github"].startswith(
            "https://github.com/"
        ):
            return False
        if (
            (len(info["discord"]) > 50)
            or (len(info["github"]) > 0)
            and "https://github.com/" not in info["github"]
        ):
            return False
        if len(info["website"]) > 0 and not (
            info["website"].startswith("http://")
            or info["website"].startswith("https://")
        ):
            return False
        self.cur.execute(
            "INSERT OR REPLACE INTO PROFILES(userid, website, github, discord, recit) VALUES (?, ?, ?, ?, ?)",
            [
                who,
                info["website"],
                info["github"],
                info["discord"],
                info["description"],
            ],
        )
        self.commit()
        return True

    def get_user_profile(self, login, api=None):
        query = self.cur.execute(
            "SELECT * FROM USERS LEFT JOIN PROFILES ON PROFILES.userid = USERS.id WHERE name = ?",
            [str(login)],
        )
        ret = query.fetchone()
        if api and ret is None:
            ret_status, ret_data = api.get_unknown_user(login)
            if ret_status != 200:
                return None
            self.create_user(ret_data, find_correct_campus(ret_data))
            return self.get_user_profile(login)
        return ret

    def get_user_profile_id(self, login):
        """
        :param login: Login 42 id
        :return: SELECT * FROM USERS
        """
        query = self.cur.execute(
            "SELECT * FROM USERS LEFT JOIN PROFILES ON PROFILES.userid = USERS.id WHERE USERS.id = ?",
            [login],
        )
        return query.fetchone()
