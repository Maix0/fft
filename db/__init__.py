import config

from .admins import AdminDb
from .cookies import CookieDb
from .custom_image import CustomImageDb
from .deadpc import DeadPcDb
from .friend import FriendDb
from .note_access import NoteAccessDb
from .notes import NoteDb
from .piscine import PiscineDb
from .piscine_date import PiscineDateDb
from .profile import ProfileDb
from .silent import SilentDb
from .themes import ThemeDb
from .tutor import TutorDb
from .tutor_station import TutorStationDb
from .user import UserDb
from .user_tag import UserTagDb
from .whitelist import WhitelistDb


class Db(
    AdminDb,
    CookieDb,
    CustomImageDb,
    DeadPcDb,
    FriendDb,
    NoteAccessDb,
    NoteDb,
    PiscineDateDb,
    PiscineDb,
    ProfileDb,
    SilentDb,
    ThemeDb,
    TutorDb,
    TutorStationDb,
    UserDb,
    UserTagDb,
    WhitelistDb,
):
    def __init__(self, filename=config.db_path):
        super().__init__(filename)
