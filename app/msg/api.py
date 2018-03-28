from .import msg
from app import db, cache, filter
from app.model import Msg, Comment, User, Zan
from flask import request, jsonify

'''
敏感信息拦截器
keywords只能支持绝对路径???
'''
f = filter.DFAFilter()
f.parse('C:\\Users\\84074\\PycharmProjects\\WXapp\\app\\keywords')
# f.parse('keywords')


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


'''
@input:
{
    msgid:"",
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
    visible = receive['visible']
    comment = Comment(msg_id=msgid, author_id=openid, content=content, target_id=targetid, time=datetime, anonymous=anonymous, visible=visible)
    db.session.add(comment)
    #   try:
    db.session.commit()
    # except BaseException as e:
    #     return 'failed'
    #     print(e)
    # else:
    return 'success'


'''
@input:
{msgid:""}
@ouput:
{
    commentlist:
    [
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
        {},…
    ]
}
'''


@msg.route("/getComments/", methods=['post'])
def get_comments():
    receive = request.get_json()
    msgid = receive['msgid']
    #comment_dict = [i.get_dict() for i in comments]
    return jsonify({'commentlist': getcomments(int(msgid))})


'''
@input:
msgid
@output:
comment_dict

处理评论获取，方便根据msgid进行缓存
'''


@cache.memoize(timeout=3600)
def getcomments(msgid):
    comments = db.session.query(Comment).filter_by(msg_id=msgid).order_by(db.desc(Comment.time))
    comment_dict = []
    for i in comments:
        i = i.get_dict()
        i['content'] = f.filter(i['content'])
        i['snickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['onickname'] = db.session.query(User.nickname).filter_by(openid=i['target_id']).first().nickname
        comment_dict.append(i)
    return comment_dict



'''
@input:
{indexf:"",indext:""}
@output:
{
    msglist:[
            {
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
             zan_status:0/1,
             hit_times:""
             },
             {},…
             ]
}
'''


@msg.route("/getMsg/", methods=['post'])
def get_msg():
    receive = request.get_json()
    indexf = receive['indexf']
    indext = receive['indext']
    string = getmsg(int(indexf), int(indext))
    #print(string)
    return jsonify({'msglist': string})


'''
获取信息，方便根据索引进行缓存
'''


@cache.memoize(timeout=300)
def getmsg(indexf, indext):
    msgs = db.session.query(Msg).order_by(db.desc(Msg.time)).offset(indexf).limit(int(indext) - int(indexf) + 1)
    msglist = []
    for i in msgs:
        i = i.get_dict()
        i['content'] = f.filter(i['content'])
        i['nickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['head_img'] = db.session.query(User.head_img).filter_by(openid=i['author_id']).first().head_img
        i['comment_num'] = db.session.query(Comment).filter_by(msg_id=i['id']).count()
        zan_status = db.session.query(Zan.status).filter_by(msg_id=i['id'], author_id=i['author_id']).first()
        if zan_status != None:
            zan_status = zan_status.status

        i['zan_status'] = zan_status
        msglist.append(i)
    return msglist


'''
@input:
{
  "user_likes": {
    "user_id": "8120381027410380412",
    "like_doing": [
      {
        "msg_id": "13241124",
        "like_flag": 0
      },
      {
        "msg_id": "12412123",
        "like_flag": 1
      },
      {
        "msg_id": "34322",
        "like_flag": 1
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
    like_list = string['like_doing']
    for i in like_list:
        msg_id = i['msg_id']
        like_flag = i['like_flag']
        zan = Zan(msg_id=msg_id, author_id=openid, status=bool(like_flag))
        db.session.add(zan)
        msg = Msg.query.filter_by(id=msg_id).first()
        msg.score = msg.score - 1 + 2*int(like_flag)
        db.session.add(msg)
        db.session.commit()
    return 'success'



'''
@intput:
{
    openid:""
    nickname:""
    head_img:""
    label:""
}
@output:
signal
说明：
    供所有用户信息的操作 修改/新增
'''


@msg.route('/getUserInfo/',methods=['post'])
def get_user_info():
    receive = request.get_json()
    openid = receive['openid']
    nickanem = receive['nickname']
    head_img = receive['head_img']
    label = receive['label']
    user = User(openid=openid, nickname=nickanem, head_img=head_img, label=label)
    # raw_user = User.query.filer_by(openid=openid).first()
    # if raw_user != None:
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


@msg.route('/getHotMsg/',methods=['post'])
def get_hot_msg():
    receive = request.get_json()
    openid = receive['openid']
    indexf = receive['indexf']
    indext = receive['indext']
    return jsonify({'msglist': gethotmsg(indexf, indext)})


'''
    可以根据index来进行缓存
    不需要手动删除缓存，随着时间自己失效即可
    因为数据库设置time events 计算综合得分
    根据距计算时间的值、score、评论数、点击量四个变量来建立模型进行热门推荐的得分计算
'''


@cache.momize(timeout=3600)
def gethotmsg(indexf, indext):
    msg = db.session.query(Msg).order_by(db.desc(Msg.overall_score)).offset(indexf).limit(int(indext) - int(indexf) + 1)
    msglist = []
    for i in msg:
        i = i.get_dict()
        i['content'] = f.filter(i['content'])
        i['nickname'] = db.session.query(User.nickname).filter_by(openid=i['author_id']).first().nickname
        i['head_img'] = db.session.query(User.head_img).filter_by(openid=i['author_id']).first().head_img
        i['comment_num'] = db.session.query(Comment).filter_by(msg_id=i['id']).count()
        zan_status = db.session.query(Zan.status).filter_by(msg_id=i['id'], author_id=i['author_id']).first()
        if zan_status != None:
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
    indexf = receive['indexf']
    indext = receive['indext']
    msglist = []
    return jsonify({'msglist':msglist})