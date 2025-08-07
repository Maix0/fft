import config

from .admins import AdminDb
from .cookies import CookieDb
from .custom_image import CustomImageDb
from .deadpc import DeadPcDb
from .friend import FriendDb
from .note_access import NoteAccessDb
from .piscine import PiscineDb
from .piscine_date import PiscineDateDb
from .profile import ProfileDb
from .silent import SilentDb
from .themes import ThemeDb
from .tutor_station import TutorStationDb
from .tutor import TutorDb
from .user_tag import UserTagDb
from .user import UserDb
from .whitelist import WhitelistDb


class Db(
    AdminDb,
    CookieDb,
    CustomImageDb,
    DeadPcDb,
    FriendDb,
    NoteAccessDb,
    PiscineDateDb,
    PiscineDb,
    ProfileDb,
    SilentDb,
    ThemeDb,
    TutorStationDb,
    TutorDb,
    UserDb,
    UserTagDb,
    WhitelistDb,
):
    def __init__(self, filename=config.db_path):
        super().__init__(filename)
