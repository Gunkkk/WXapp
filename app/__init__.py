from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cache import Cache
import redis
from celery import Celery

pool = redis.ConnectionPool(host='127.0.0.1', port='6379', db=1)
redis_connection = redis.Redis(connection_pool=pool)

cache = Cache(config={
        "CACHE_TYPE": "redis",
        "CACHE_REDIS_HOST": "127.0.0.1",
        "CACHE_REDIS_PORT": 6379,
        "CACHE_REDIS_DB": 0,
        "CACHE_REDIS_PASSWORD": ""
})
app = Flask(__name__)
app.config.from_pyfile('dbconfig.py')

celery = Celery('tasks', broker='redis://localhost:6379/2', backend='redis://localhost:6379/2')
celery.conf.update(app.config)

db = SQLAlchemy(app)
from app import model
# 新建表前必须导入模型
db.create_all()
cache.init_app(app)

from .msg import msg
app.register_blueprint(msg, url_prefix='/msg')
from .user import user
app.register_blueprint(user, url_prefix='/user')
from . verifyStage import verify
app.register_blueprint(verify, url_prefix='/verify')
