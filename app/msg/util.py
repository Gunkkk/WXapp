from app import redis_connection, db
from app.model import MsgInfo, Comment, CommentSecond

HIT_TIME_PER = 10


def get_hit(msg_id):
    # pipe = redis_connection.pipeline()
    # redis_connection.hincrby('hit_time', msg_id, amount=1)
    if redis_connection.hexists('hit_time', msg_id):
        times = redis_connection.hget('hit_time', msg_id)
        if times > HIT_TIME_PER:
            redis_connection.hset('hit_time', msg_id, 0)
            msg_info = MsgInfo.query.filter_by(msg_id=msg_id).first()
            if msg_info is None:
                msg_info = MsgInfo(msg_id=msg_id, hit_times=times)
            else:
                msg_info.hit_times = msg_info.hit_times + times
            db.session.add(msg_info)
            db.session.commit()
        else:
            redis_connection.hincrby('hit_time', msg_id, amount=1)
    else:
        redis_connection.hset('hit_time', msg_id, 1)

# pipe.execute()


def comment_author_num_operation(msg_id, author_id):
    comment = Comment.query.filter_by(msg_id=msg_id, author_id=author_id).first()
    comment_sec = CommentSecond.query.filter_by(msg_id=msg_id, author_id=author_id).first()
    if comment is None and comment_sec is None:
        msg_info = MsgInfo.query.filter_by(msg_id=msg_id).first()
        if msg_info is None:
            msg_info = MsgInfo(msg_id=msg_id, comment_author_num=1)
        else:
            msg_info.comment_author_num += 1
        db.session.add(msg_info)
        db.session.commit()

