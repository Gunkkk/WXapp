
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:h124365@localhost:3306/wxapp?charset=utf8'
SQLALCHEMY_TRACK_MODIFICATIONS = True

SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 1
SQLALCHEMY_MAX_OVERFLOW = 20

JOBS = [
    {
        'id': 'job1',
        'func': 'app.schedule:overallCalculate',
        'args': '',
        'trigger': 'interval',
        'seconds': 10
    }
]
SCHEDULER_API_ENABLED = True


