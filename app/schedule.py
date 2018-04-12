from app.msg.task import *


def overall_calculate():
    msg_info = MsgInfo.query.yield_per(100)
    for i in msg_info:
        overall_score_calculate.delay(i.get_dict())
    print(datetime.datetime.now(), 'calculate completed!')
