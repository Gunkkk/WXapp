from . import user
from app import db
from app.model import User, UserVerify
from flask import request, jsonify
import requests
import hashlib
import json

'''
8	getUserInfo
11	setUserInfo
16	applyUserType
 
'''


'''
@intput:
{
    code:"",
    nickname:"",
    head_img:""
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
            "label":"",
            "reply_num":""
        }
    }
}/false
说明：
    用户登录操作
'''

appid = 'wx045b0b63f6b9f5f9'
secret = '8e38d54e64e4f0fe89418148a7982bb3'


def check_legal(openid_md5):
    user = db.session.query(User).filter_by(openid=openid_md5).first()
    if user is None:
        return False
    else:
        return True


@user.route('/getUserInfo/', methods=['post'])
def get_user_info():
    receive = request.get_json()
    code = receive['code']
    url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % \
          (appid, secret, code)

    # {"session_key":"S1V0xJ88wooatu6I\/Hao4w==","openid":"omyxV4wFovxLS2CtuljRIIKiIcjU"}
    r = requests.get(url)
    returns = json.loads(r.text)

    if 'openid' not in returns.keys():
        return 'false'
    session_key = returns['session_key']
    openid = returns['openid']
    nickname = receive['nickname'].encode('utf-8')
    head_img = receive['head_img']
    result = dict()
    openid = hashlib.md5(openid.encode(encoding='UTF-8')).hexdigest() # MD5加密
    user = User.query.filter_by(openid=openid).first()
    if user is None:
        user = User(openid=openid, nickname=nickname, head_img=head_img)
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
            "label":"",
            "reply_num":
            "type": 
            //不必全给出
    }
@output
signal

修改用户信息       
'''


@user.route('/setUserInfo/', methods=['post'])
def set_user_info():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    user = User.query.filter_by(openid=openid).first()
    if 'nickname' in receive.keys():
        user.nickname = receive['nickname'].encode('utf-8')
    if 'head_img' in receive.keys():
        user.head_img = receive['head_img']
    if 'label' in receive.keys():
        user.label = receive['label']
    if 'reply_num' in receive.keys():
        user.reply_num = receive['reply_num']
    if 'is_group' in receive.keys():
        user.reply_num = receive['type']

    db.session.add(user)
    db.session.commit()
    return 'success'


'''
@input:
{
    openid:"",
    content:"",
    type:"",
    picture:"",
    datetime:""
}
@output:
signal

提交用户类型修改申请
'''


@user.route('/applyUserType/', methods=['post'])
def apply_user_type():
    receive = request.get_json()
    openid = receive['openid']
    if openid is None or not check_legal(openid):
        return 'failed'
    content = receive['content']
    type = receive['type']
    datetime = receive['datetime']
    if 'picture' in receive.keys():
        picture = receive['picture']
    else:
        picture = None
    user_verify = UserVerify(openid=openid, content=content, time=datetime, picture=picture, user_type=type)
    db.session.add(user_verify)
    db.session.commit()
    return 'success'
