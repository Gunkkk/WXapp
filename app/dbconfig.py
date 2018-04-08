from datetime import timedelta
from celery.schedules import crontab


SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:h124365@localhost:3306/wxapp?charset=utf8'
SQLALCHEMY_TRACK_MODIFICATIONS = True

SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 1
SQLALCHEMY_MAX_OVERFLOW = 20

JOBS = [
    {
        'id': 'job1',
        'func': 'app.schedule:overall_calculate',
        'args': '',
        'trigger': 'interval',
        'seconds': 600
    }
]
SCHEDULER_API_ENABLED = True

# CELERY_BROKER_URL = 'redis://localhost:6379/2'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'  # 存储任务状态和运行结果
