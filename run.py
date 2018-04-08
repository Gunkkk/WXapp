from app import app
from flask_apscheduler import APScheduler
if __name__ == '__main__':
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run()
   # app.run(host='0.0.0.0', ssl_context=('/root/Nginx/1_hwb.yibutech.cn_bundle.crt','/root/Nginx/2_hwb.yibutech.cn.key'), port=443)

# celery -A app:celery worker -l info -P eventlet