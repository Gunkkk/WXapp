from .import msg
from app import db, cache, filter, redis_connection
from app.model import Msg, Comment, User, Zan, MsgInfo, CommentSecond, ZanComment
from flask import request, jsonify
import requests
import json
import hashlib
from app.msg.task import *
'''
api:
1	addMsg
2	addComment
3	addCommentSec
4	addScores
5	getComments
6	getMsg
7	
8	getUserInfo
9	getHotMsg
10	getRecom
11	setUserInfo
'''


'''
敏感信息拦截器
keywords只能支持绝对路径???
'''
f = filter.DFAFilter()
f.parse('C:\\Users\\84074\\PycharmProjects\\WXapp\\app\\keywords') # 采用绝对地址
#f.parse('/root/venvtest/app/keywords')

# f.parse('keywords')


'''
@input:
openid_md5
@output:
true/false

进行身份验证进行api访问拦截
'''


@cache.memoize(timeout=3600)
def check_legal(openid_md5):
    user = db.session.query(User).filter_by(openid=openid_md5).first()
    if user is None:
        return False
    else:
        return True


@msg.route("/")
def hello_world():
    return "hello world"


'''
@input:
{
    openid:"",
    content:"",
    datetime:"2018-03-21 21:32:23",
    anonymous:0/1,
    longitude:"",
    latitude:""
}
@output:
signal
'''


@msg.route("/addMsg/", methods=['post'])
def add_msg():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    content = receive['content']
    datetime = receive['datetime']
    anonymous = receive['anonymous']
    longitude = receive['longitude']
    latitude = receive['latitude']

    #cache.delete_memoized(getmsg)
    # 删除缓存
    # 被遗忘而不会被删除 设定较短生存周期
    msg = Msg(author_id=openid, content=content,  # 需要一个触发器进行msginfo的初始化
              time=datetime, anonymous=anonymous,
              longitude=longitude, latitude=latitude)
    db.session.add(msg)
    #try:
    db.session.commit()
    # except BaseException as e:
    #     return 'failed'
    #     print(e)
    # else:
    return 'success'


'''
@input:
{indexf:"",indext:"",openid:""}
@output:
{
    msglist:[
            {
             id:"",
             author_id:"",
             nickname:"",
             head_img:"",
             content:"",
             time:"",
             score:"",
             anonymous:0/1,
             longitude:"",
             latitude:"",
             comment_num:"",
             zan_status:0/1/2,
             hit_times:"",
             picture:""
             },
             {},…
             ]
}
'''


@msg.route("/getMsg/", methods=['post'])
def get_msg():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    indexf = receive['indexf']
    indext = receive['indext']
    string = getmsg(int(indexf), int(indext), openid)
    #print(string)
    return jsonify({'msglist': string})


'''
获取信息，方便根据索引进行缓存
'''


#@cache.memoize(timeout=300)
def getmsg(indexf, indext,openid):
    msgs = db.session.query(Msg).order_by(db.desc(Msg.time)).offset(indexf).limit(int(indext) - int(indexf) + 1)
    msglist = []
    for i in msgs:
        i = i.get_dict()
        id = i['id']
        msg_info = db.session.query(MsgInfo).filter_by(msg_id=id).first()
        if msg_info is not None:
            i['score'] = msg_info.score
            i['hit_times'] = msg_info.hit_times
        else:
            i['score'] = 0
            i['hit_times'] = 0
        i['time'] = i['time'].strftime("%Y-%m-%d %H:%M:%S")
        i['content'] = f.filter(i['content'])
        i['nickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['head_img'] = db.session.query(User.head_img).filter_by(openid=i['author_id']).first().head_img
        i['comment_num'] = db.session.query(Comment).filter_by(msg_id=i['id']).count()
        zan_status = db.session.query(Zan.status).filter_by(msg_id=i['id'], author_id=openid).first()
        if zan_status is not None:
            zan_status = zan_status.status

        i['zan_status'] = zan_status
        msglist.append(i)
    return msglist


'''
@input:
{
    msgid:"",
    openid:"",
    content:"",
    datetime:"",
    anonymous:0/1,
    visible:0/1
}
@output:
signal
'''


@msg.route("/addComment/", methods=['post'])
def add_comment():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    msgid = receive['msgid']


    #cache.delete_memoized(getcomments, int(msgid))
    # 删除缓存
    # 不将msgid转为int缓存无法删除

    content = receive['content']
    datetime = receive['datetime']
    anonymous = receive['anonymous']
    visible = receive['visible']
    comment = Comment(msg_id=msgid, author_id=openid, content=content, time=datetime, anonymous=anonymous, visible=visible,score=0)
    db.session.add(comment)
    #   try:
    db.session.commit()
    comment_author_num_operation.delay(msgid, openid)  # 最好使用异步执行
    # except BaseException as e:
    #     return 'failed'
    #     print(e)
    # else:
    return 'success'


'''
@input:
{
    msgid:"",
    indexf:"",
    indext:"",
    openid:"",
    order:"time/score"
}
@ouput:
{
    commentlist:
    [
        {
        author_id:"",
        target_id:"",
        snickname:"",
        content:"",
        time:"",
        anonymous:0/1,
        visible:0/1,
        head_img:"",
        score:"",
        zan_status:0/1/2,
        comments_num:"",
        comments:[
                    {
                        author_id:"",
                        target_id:"",
                        snickname:"",
                        onickname:"",
                        content:"",
                        time:"",
                        anonymous:0/1,
                        visible:0/1
                    },
                    {}]
        },
        {},…
    ]
}
'''


@msg.route("/getComments/", methods=['post'])
def get_comments():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None:
        return 'failed'
    if openid is None or not check_legal(openid):
        return 'failed'
    msgid = receive['msgid']
    get_hit.delay(msgid)  # 使用异步执行
    indexf = receive['indexf']
    indext = receive['indext']
    order = receive['order']
     #comment_dict = [i.get_dict() for i in comments]
    return jsonify({'commentlist': getcomments(int(msgid), int(indexf), int(indext), openid, order)})


'''
@input:
msgid,indexf,indext,openid,order
@output:
comment_dict

处理评论获取，方便根据msgid进行缓存
'''


#@cache.memoize(timeout=3600)
def getcomments(msgid, indexf, indext,openid,order):
    if order == 'time':
        comments = db.session.query(Comment).filter_by(msg_id=msgid).order_by(db.desc(Comment.time)).offset(indexf).limit(int(indext) - int(indexf) + 1)
    else:
        comments = db.session.query(Comment).filter_by(msg_id=msgid).order_by(db.desc(Comment.score)).offset(indexf).limit(int(indext) - int(indexf) + 1)
    comment_dict = []
    for i in comments:
        i = i.get_dict()
        i['content'] = f.filter(i['content'])
        i['snickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['comments'] = getcommentssec(i['id'])
        i['head_img'] = db.session.query(User.head_img).filter_by(openid=i['author_id']).first().head_img
        zan_status = db.session.query(ZanComment.status).filter_by(comment_id=i['id'], author_id=openid).first()
        if zan_status is not None:
            zan_status = zan_status.status

        i['zan_status'] = zan_status
        i['time'] = i['time'].strftime("%Y-%m-%d %H:%M:%S")
        i['comments_num'] = db.session.query(CommentSecond).filter_by(msg_id=i['id']).count()
        comment_dict.append(i)
    return comment_dict


'''
@input:
{
    msgid:"",
    commentid:"",
    openid:"",
    targetid:"",
    content:"",
    datetime:"",
    anonymous:0/1,
    visible:0/1
}
@output:
signal
'''


@msg.route("/addCommentSec/", methods=['post'])
def add_comment_second():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    commentid = receive['commentid']
    msgid = receive['msgid']
    cache.delete_memoized(getcommentssec, int(commentid))
    commentid = receive['commentid']
    # 删除缓存
    # 不将id转为int缓存无法删除
    targetid = receive['targetid']
    content = receive['content']
    datetime = receive['datetime']
    anonymous = receive['anonymous']
    visible = receive['visible']
    commentsec = CommentSecond(msg_id=msgid, comment_id=commentid, author_id=openid, content=content, target_id=targetid, time=datetime, anonymous=anonymous, visible=visible)
    db.session.add(commentsec)
    #   try:
    db.session.commit()
    # except BaseException as e:
    #     return 'failed'
    #     print(e)
    # else:
    return 'success'


'''
@input:
commentid
@output:
comment_dict
    {
        author_id:"",
        target_id:"",
        snickname:"",
        onickname:"",
        content:"",
        time:"",
        anonymous:0/1,
        visible:0/1
    }
处理二级评论获取，方便根据commentid进行缓存
'''


@cache.memoize(timeout=3600)
def getcommentssec(commentid):
    comments = db.session.query(CommentSecond).filter_by(comment_id=commentid).order_by(db.desc(CommentSecond.time))
    comment_dict = []
    for i in comments:
        i = i.get_dict()
        i['content'] = f.filter(i['content'])
        i['time'] = i['time'].strftime("%Y-%m-%d %H:%M:%S")
        i['snickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['onickname'] = db.session.query(User.nickname).filter_by(openid=i['target_id']).first().nickname
        comment_dict.append(i)
    return comment_dict


'''
@input:
{
  "user_likes": 
  {
    "user_id": "8120381027410380412",
    "like_doing": 
    [
      {
        "msg_id": "13241124",
        "like_flag": 0,
        "score":-1
      },
      {
        "msg_id": "12412123",
        "like_flag": 1
        "score":1
      },
      {
        "msg_id": "34322",
        "like_flag": 2
        "score": 1
      }
    ],
    "like_doing_sec":
    [
      {
        "comment_id":"",
        "like_flag":1,
        "score":1
      },
      {
        "comment_id":"",
        "like_flag":2,
        "score":-1
      }
    
    ]
  }
}
@output:
signal
'''


@msg.route('/addScores/', methods=['post'])
def add_scores():
    receive = request.get_json()
    string = receive['user_likes']
    openid = string['user_id']
    if openid is None or not check_legal(openid):
        return 'failed'
    like_list = string['like_doing']
    like_list_sec = string['like_doing_sec']
    for i in like_list:
        msg_id = i['msg_id']
       # cache.delete_memoized(getcomments, int(msg_id))  # 删除缓存
        like_flag = i['like_flag']
        score = int(i['score'])
        zan = Zan.query.filter_by(msg_id=msg_id, author_id=openid).first()
        if zan==None:
            zan = Zan(msg_id=msg_id, author_id=openid, status=like_flag)
        else:
            zan.status = like_flag
        db.session.add(zan)

        msg_info = MsgInfo.query.filter_by(msg_id=msg_id).first()
        if msg_info is None:
            msg_info = MsgInfo(msg_id=msg_id, score=score ,overall_score=0, comment_author_num=0, hit_times=0)
        else:
            msg_info.score = msg_info.score + score
        db.session.add(msg_info)
        db.session.commit()
    for i in like_list_sec:
        comment_id = i['comment_id']
        cache.delete_memoized(getcommentssec, int(comment_id))  # 删除缓存
        like_flag = i['like_flag']
        score = int(i['score'])
        zan_comment = ZanComment.query.filter_by(comment_id=comment_id, author_id=openid).first()
        if zan_comment is None:
            zan_comment=ZanComment(comment_id=comment_id, author_id=openid, status=like_flag)
        else:
            zan_comment.status = like_flag
        db.session.add(zan_comment)

        comment = Comment.query.filter_by(id=comment_id).first()
        comment.score = comment.score + score
        db.session.add(comment)
        db.session.commit()
    return 'success'



'''
@intput:
{
    code:"",
}
@output:
{
    "result":
    {
        "user_type":"new"/"old",
        "user_info":
        {
            "openid":"",
            "nickname":"",
            "head_img:"",
            "label":""
        }
    }
}/false
说明：
    用户登录操作
'''

appid = 'wx045b0b63f6b9f5f9'
secret = '8e38d54e64e4f0fe89418148a7982bb3'


@msg.route('/getUserInfo/', methods=['post'])
def get_user_info():
    receive = request.get_json()
    code = receive['code']
    url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % \
          (appid, secret, code)

    ## {"session_key":"S1V0xJ88wooatu6I\/Hao4w==","openid":"omyxV4wFovxLS2CtuljRIIKiIcjU"}
    r = requests.get(url)
    returns = json.loads(r.text)

    if 'openid' not in returns.keys():
        return 'false'
    session_key = returns['session_key']
    openid = returns['openid']
    result = dict()
    openid = hashlib.md5(openid.encode(encoding='UTF-8')).hexdigest() # MD5加密
    user = User.query.filter_by(openid=openid).first()
    if user is None:
        user = User(openid=openid)
        db.session.add(user)
        db.session.commit()
        user.openid = openid
        result['user_type'] = 'new'
    else:
        result['user_type'] = 'old'
    user = user.get_dict()

    result['user_info'] = user
    # raw_user = User.query.filer_by(openid=openid).first()
    # if raw_user != None:
    result['session_key'] = session_key
    return jsonify({"result": result})

'''
@input:
    {
            "openid":"",
            "nickname":"",
            "head_img":"",
            "label":""
    }
@output
signal

修改用户信息       
'''


@msg.route('/setUserInfo/', methods=['post'])
def set_user_info():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    nickname = receive['nickname']
    head_img = receive['head_img']
    label = receive['label']
    user = User.query.filter_by(openid=openid).first()
    user.nickname = nickname
    user.head_img = head_img
    user.label = label
    db.session.add(user)
    db.session.commit()
    return 'success'


'''
@input：
{
    openid:"",
    indexf:"",
    indext:""
}
@output：
msglist:

获取热门信息
暂时根据score\时间排序推荐
'''


@msg.route('/getHotMsg/', methods=['post'])
def get_hot_msg():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    indexf = receive['indexf']
    indext = receive['indext']
    return jsonify({'msglist': gethotmsg(indexf, indext,openid)})


'''
获取实时热榜  
    {
    msglist:[
            {
             id:"",
             author_id:"",
             nickname:"",
             head_img:"",
             content:"",
             time:"",
             score:"",
             anonymous:0/1,
             longitude:"",
             latitude:"",
             comment_num:"",
             zan_status:0/1/2,
             hit_times:"",
             picture:"",
             overall_scores:"",
             comment_author_num:""
             },
             {},…
             ]
}
'''


#@cache.memoize(timeout=3600)
def gethotmsg(indexf, indext, openid):
    msg_info = db.session.query(MsgInfo).order_by(db.desc(MsgInfo.overall_score)).offset(indexf).limit(int(indext) - int(indexf) + 1)
    msglist = list()
    for i in msg_info:
        i = i.get_dict()
        msg_id = i['msg_id']
        msg = db.session.query(Msg).filter_by(id=msg_id).first()
        msg = msg.get_dict()
        i['id'] = msg_id
        i['author_id'] = msg['author_id']
        i['content'] = f.filter(msg['content'])
        i['time'] = msg['time'].strftime("%Y-%m-%d %H:%M:%S")
        i['anonymous'] = msg['anonymous']
        i['latitude'] = msg['latitude']
        i['longitude'] = msg['longitude']
        i['picture'] = msg['picture']
        i['nickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['head_img'] = db.session.query(User.head_img).filter_by(openid=i['author_id']).first().head_img
        i['comment_num'] = db.session.query(Comment).filter_by(msg_id=i['id']).count()

        zan_status = db.session.query(Zan.status).filter_by(msg_id=i['id'], author_id=openid).first()
        if zan_status is not None:
            zan_status = zan_status.status

        i['zan_status'] = zan_status
        msglist.append(i)
    return msglist


'''
@input：
{
    openid:"",
    indexf:"",
    indext:""
}
@output：
msglist:

获取推荐信息
'''


@msg.route('/getRecom/',methods=['post'])
def get_recom():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    indexf = receive['indexf']
    indext = receive['indext']
    msglist = []
    return jsonify({'msglist':msglist})



'''
@input:
{
    openid:"",
}
@output:
{
    reply:
    {
    
    }

}
'''


@msg.route('/getReply/',methods=['post'])
def get_reply():
    receive = request.get_json()