from app import redis_connection, db, celery
from app.model import MsgInfo, Comment, CommentSecond, MsgInfoLast, Msg, Reply, User
import datetime
import math
HIT_TIME_PER = 1


@celery.task
def get_hit(msg_id):
    # pipe = redis_connection.pipeline()
    # redis_connection.hincrby('hit_time', msg_id, amount=1)
    if redis_connection.hexists('hit_time', msg_id):
        times = int(redis_connection.hget('hit_time', msg_id))
        if times >= HIT_TIME_PER:
            redis_connection.hset('hit_time', msg_id, 0)
            times += 1
            msg_info = MsgInfo.query.filter_by(msg_id=msg_id).first()
            if msg_info is None:
                msg_info = MsgInfo(msg_id=msg_id, hit_times=times, score=0, comment_author_num=0, overall_score=0)
            else:
                msg_info.hit_times = msg_info.hit_times + times
            db.session.add(msg_info)
            db.session.commit()
        else:
            redis_connection.hincrby('hit_time', msg_id, amount=1)
    else:
        redis_connection.hset('hit_time', msg_id, 1)

# pipe.execute()


@celery.task
def comment_author_num_operation(msg_id, author_id):
    comment = Comment.query.filter_by(msg_id=msg_id, author_id=author_id).count()
    comment_sec = CommentSecond.query.filter_by(msg_id=msg_id, author_id=author_id).count()
    r = int(comment) + int(comment_sec)
    if r == 1:
        msg_info = MsgInfo.query.filter_by(msg_id=msg_id).first()
        if msg_info is None:
            msg_info = MsgInfo(msg_id=msg_id, comment_author_num=1, score=0, overall_score=0, hit_times=0)
        else:
            msg_info.comment_author_num = int(msg_info.comment_author_num) + 1
        db.session.add(msg_info)
        db.session.commit()



'''
热度值计算
t0 = last_reply_time
time = t-t0  /三天（72h）
zan_num
com_num
hit
value = (e^-time*value0+△com_num*△zan_num/5 +log10(△hit+1)*4))
 
'''


@celery.task
def overall_score_calculate(msg_info):
    i = msg_info
    msg_id = i['msg_id']
    msg_info_last = MsgInfoLast.query.filter_by(msg_id=msg_id).first()
    score = i['score']
    hit_times = i['hit_times']
    comment_author_num = i['comment_author_num']
    overall_score = i['overall_score']
    if msg_info_last is not None:
        score_last = msg_info_last.score
        hit_times_last = msg_info_last.hit_times
        comment_author_num_last = msg_info_last.comment_author_num
    # overall_score_last = msg_info_last.overall_score
        msg_info_last.score = score
        msg_info_last.overall_score = overall_score
        msg_info_last.hit_times = hit_times
        msg_info_last.comment_author_num = comment_author_num

    else:
        score_last = 0
        hit_times_last = 0
        comment_author_num_last = 0
    # overall_score_last = 0
        msg_info_last = MsgInfoLast(msg_id=msg_id, score=score, overall_score=overall_score, hit_times=hit_times,
                                    comment_author_num=comment_author_num)
    db.session.add(msg_info_last)
    db.session.commit()
    time = db.session.query(Msg.time).filter_by(id=msg_id).first().time
    now = datetime.datetime.now()

    seconds = (now - time).seconds
    delta_days = round(seconds / (3600 * 24), 4)
    delta_score = score - score_last
    delta_hit_times = hit_times - hit_times_last
#  print(delta_hit_times, 'x', hit_times, 'x', hit_times_last, 'dddddddddddddddddd')  # log10(delta_hit_times)报错 监控
    delta_comment_author_num = comment_author_num - comment_author_num_last
    value0 = overall_score
    value = (math.e ** (-1 * delta_days) * value0 + delta_comment_author_num * delta_score / 5 +
             math.log10(delta_hit_times + 1) * 4)

    # i['overall_score'] = value
    result = MsgInfo.query.filter_by(msg_id=msg_id).first()
    print(result.overall_score)
    result.overall_score = value
    db.session.add(result)
    db.session.commit()


'''
消息回复提示
@input 
msg_id, open_id

'''


@celery.task
def add_msg_reply(msg_id, open_id):
    msg = Msg.query.filter_by(id=msg_id).first()
    if msg is None:
        return
    else:
        target_id = msg.author_id
    comment = db.session.query(Comment).filter_by(msg_id=msg_id, author_id=open_id).order_by(db.desc(Comment.time))\
        .first()  # 可靠吗？
    if comment is None:
        return
    else:
        comment_id = comment.id

    reply = Reply(msg_id=msg_id, target_id=target_id, comment_id=comment_id, is_read=False)
    user = User.query.filter_by(openid=open_id).first()
    if user.reply_num is None:
        user.reply_num = 0
    user.reply_num = user.reply_num + 1
    db.session.add(user)
    db.session.add(reply)
    db.session.commit()
    value = str(msg_id)+'_'+str(comment_id)
    redis_connection.set(str(target_id), value, ex=300)  # 过期时间为ex 秒


'''
评论回复提示
@input
comment_id, open_id
'''


@celery.task
def add_comment_reply(comment_id, open_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment is None:
        return
    else:
        target_id = comment.author_id
        msg_id = comment.msg_id
    sec_comment = db.session.query(CommentSecond).filter_by(comment_id=comment_id, author_id=open_id).\
        order_by(db.desc(CommentSecond.time)).first()
    if sec_comment is None:
        return
    else:
        sec_comment_id = sec_comment.id

    reply = Reply(msg_id=msg_id, target_id=target_id, comment_id=comment_id, sec_comment_id=sec_comment_id,
                  is_read=False)
    user = User.query.filter_by(openid=open_id).first()
    if user.reply_num is None:
        user.reply_num = 0
    user.reply_num = user.reply_num + 1
    db.session.add(user)
    db.session.add(reply)
    db.session.commit()
    value = str(msg_id)+'_'+str(comment_id)+'_'+str(sec_comment_id)
    redis_connection.set(target_id+'_sec', value, ex=300)  # 过期时间为ex 秒
