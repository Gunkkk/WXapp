from app.msg.task import *
import time as t


def overall_calculate():
    print(datetime.datetime.now(), 'calculate start!')
    count = MsgInfo.query.count()
    for i in range(count):
        msg_info = MsgInfo.query.order_by(MsgInfo.msg_id).limit(1).offset(i).first()
        print(msg_info.__dict__)
        overall_score_calculate(msg_info.__dict__)
    print(datetime.datetime.now(), 'calculate completed!')
    #
    # msg_info = db.session.query(MsgInfo).all()#yield_per(100)#.enable_eagerloads(False).order_by(MsgInfo.msg_id)
    # print(msg_info)
    # for i in msg_info:
    #     value = overall_score_calculate(i.__dict__)
    #     i.overall_score = value
    #     db.session.add(i)
    #     db.session.commit()
    # # overall_score_calculate.delay(i.get_dict())
    # db.session.commit()
    # print(datetime.datetime.now(), 'calculate completed!')


def overall_score_calculate(msg_info):
    i = msg_info
    msg_id = i['msg_id']
    msg_info_last = MsgInfoLast.query.filter_by(msg_id=msg_id).first()
    time = db.session.query(Msg.time).filter_by(id=msg_id).first().time
    score = i['score']
    hit_times = i['hit_times']
    comment_author_num = i['comment_author_num']
    overall_score = i['overall_score']
    if msg_info_last is not None:
        score_last = msg_info_last.score
        hit_times_last = msg_info_last.hit_times
        comment_author_num_last = msg_info_last.comment_author_num
        #overall_score_last = msg_info_last.overall_score
        msg_info_last.score = score
        msg_info_last.overall_score = overall_score
        msg_info_last.hit_times = hit_times
        msg_info_last.comment_author_num = comment_author_num

    else:
        score_last = 0
        hit_times_last = 0
        comment_author_num_last = 0
        #overall_score_last = 0
        msg_info_last = MsgInfoLast(msg_id=msg_id, score=score, overall_score=overall_score, hit_times=hit_times,
                                    comment_author_num=comment_author_num)
    db.session.add(msg_info_last)
    db.session.commit()
    now = datetime.datetime.now()
    seconds = (now - time).seconds
    delta_days = round(seconds / (3600 * 24), 4)
    delta_score = score - score_last
    delta_hit_times = hit_times - hit_times_last
    delta_comment_author_num = comment_author_num - comment_author_num_last
    value0 = overall_score
    value = (math.e ** (-1 * delta_days) * value0 + delta_comment_author_num * delta_score / 5 +
             math.log10(delta_hit_times + 1) * 4)
    result = MsgInfo.query.filter_by(msg_id=msg_id).first()
    result.overall_score = value
    db.session.add(result)
    db.session.commit()

