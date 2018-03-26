from .import msg
from app import db, cache
from app.model import Msg, Comment, User
from flask import request, jsonify


@msg.route("/")
def hello_world():
    return "hello world"


@msg.route("/addMsg/", methods=['post'])
def add_msg():
    receive = request.get_json()
    openid = receive['openid']
    content = receive['content']
    datetime = receive['datetime']
    anonymous = receive['anonymous']
    longitude = receive['longitude']
    latitude = receive['latitude']

    cache.delete_memoized(getmsg)
    # 删除缓存
    # 被遗忘而不会被删除 设定较短生存周期
    msg = Msg(author_id=openid, content=content,
              score=0, time=datetime, anonymous=anonymous,
              longitude=longitude, latitude=latitude )
    db.session.add(msg)
    #try:
    db.session.commit()
    # except BaseException as e:
    #     return 'failed'
    #     print(e)
    # else:
    return 'success'


@msg.route("/addComment/", methods=['post'])
def add_comment():
    receive = request.get_json()
    msgid = receive['msgid']
    cache.delete_memoized(getcomments, int(msgid))
    # 删除缓存
    # 不将msgid转为int缓存无法删除
    openid = receive['openid']
    targetid = receive['targetid']
    content = receive['content']
    datetime = receive['datetime']
    anonymous = receive['anonymous']
    comment = Comment(msg_id=msgid, author_id=openid, content=content, target_id=targetid, time=datetime, anonymous=anonymous)
    db.session.add(comment)
    #   try:
    db.session.commit()
    # except BaseException as e:
    #     return 'failed'
    #     print(e)
    # else:
    return 'success'


@msg.route("/addScore/", methods=['post'])
def add_score():
    receive = request.get_json()


@msg.route("/getComments/", methods=['post'])
def get_comments():
    receive = request.get_json()
    msgid = receive['msgid']

    #comment_dict = [i.get_dict() for i in comments]
    return jsonify({'commentlist': getcomments(int(msgid))})


@cache.memoize(timeout=3600)
def getcomments(msgid):
    comments = db.session.query(Comment).filter_by(msg_id=msgid).order_by(db.desc(Comment.time))
    comment_dict = []
    for i in comments:
        i = i.get_dict()
        i['snickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['onickname'] = db.session.query(User.nickname).filter_by(openid=i['target_id']).first().nickname
        comment_dict.append(i)
    return comment_dict


@msg.route("/getMsg/", methods=['post'])
def get_msg():
    receive = request.get_json()
    indexf = receive['indexf']
    indext = receive['indext']
    string = getmsg(int(indexf), int(indext))
    #print(string)
    return jsonify({'msglist': string})


@cache.memoize(timeout=300)
def getmsg(indexf, indext):
    msgs = db.session.query(Msg).order_by(db.desc(Msg.time)).offset(indexf).limit(int(indext) - int(indexf) + 1)
    msglist = []
    for i in msgs:
        i = i.get_dict()
        i['nickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['head_img'] = db.session.query(User.head_img).filter_by(openid=i['author_id']).first().head_img
        i['comment_num'] = db.session.query(Comment).filter_by(msg_id=i['id']).count()
        msglist.append(i)
    return msglist
