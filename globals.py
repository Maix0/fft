import redis
from api42 import Api
import config
from db import Db

r = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)
api = Api(config.key, config.secret)
