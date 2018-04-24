from app import redis_connection, celery, db
from app.model import Reply, User


@celery.task
def get_verify_reply(openid, result):

    reply = Reply(target_id=openid, is_read=False, verify_content=result)
    user = User.query.filter_by(openid=openid).first()
    if user.reply_num is None:
        user.reply_num = 0
    user.reply_num = user.reply_num + 1
    db.session.add(user)
    db.session.add(reply)
    db.session.commit()

    value = str(result)
    redis_connection.set(str(openid)+'_verify', value, ex=300)

