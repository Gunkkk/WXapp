from app import db


class Father(object):
    def get_dict(self):
        # di = {}
        # for name, value in vars(self).items():
        #     di[name] = value
        di = self.__dict__
        di.pop('_sa_instance_state')  # 自动转多一个
        return di


class Msg(db.Model, Father):
    __tablename__ = "msg"
    id = db.Column(db.BigInteger, primary_key=True)
    author_id = db.Column(db.String(40), db.ForeignKey('user.openid'))
    content = db.Column(db.String(280))
#    score = db.Column(db.Integer)
    time = db.Column(db.DateTime)
    anonymous = db.Column(db.Boolean)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    picture = db.Column(db.String(200))
#    overall_score = db.Column(db.Float)
#    hit_times = db.Column(db.BigInteger)
    type = db.Column(db.String(20))


# 需要触发器来进行初始化
class MsgInfo(db.Model, Father):
    __tablename__ = "msg_dyn_info"
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'), primary_key=True)
#    author_id = db.Column(db.String(40), db.ForeignKey('user.openid'))
#    content = db.Column(db.String(280))
    score = db.Column(db.Integer)
#    time = db.Column(db.DateTime)
#    anonymous = db.Column(db.Boolean)
#    longitude = db.Column(db.Float)
#    latitude = db.Column(db.Float)
    overall_score = db.Column(db.Float)
    hit_times = db.Column(db.BigInteger)
    comment_author_num = db.Column(db.Integer)
    # last_active_time = db.Column(db.DateTime)


class MsgInfoLast(db.Model, Father):
    __tablename__ = "msg_dyn_info_before"
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'), primary_key=True)
#   author_id = db.Column(db.String(40), db.ForeignKey('user.openid'))
#   content = db.Column(db.String(280))
    score = db.Column(db.Integer)
#    time = db.Column(db.DateTime)
#   anonymous = db.Column(db.Boolean)
#    longitude = db.Column(db.Float)
#    latitude = db.Column(db.Float)
    overall_score = db.Column(db.Float)
    hit_times = db.Column(db.BigInteger)
    comment_author_num = db.Column(db.Integer)
    # last_active_time = db.Column(db.DateTime)


class Comment(db.Model, Father):
    __tablename__ = 'comment'
    id = db.Column(db.BigInteger, primary_key=True)
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'))
    author_id = db.Column(db.String(40))
    content = db.Column(db.String(280))
    #target_id = db.Column(db.String(40))
    time = db.Column(db.DateTime)
    anonymous = db.Column(db.Boolean)
    visible = db.Column(db.Boolean)
    score = db.Column(db.Integer)


class CommentSecond(db.Model, Father):
    __tablename__ = 'comment_second'
    id = db.Column(db.BigInteger, primary_key=True)
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'))
    comment_id = db.Column(db.BigInteger, db.ForeignKey('comment.id'))
    author_id = db.Column(db.String(40))
    content = db.Column(db.String(280))
    target_id = db.Column(db.String(40))
    time = db.Column(db.DateTime)
    anonymous = db.Column(db.Boolean)
    visible = db.Column(db.Boolean)


class User(db.Model, Father):
    __tablename__ = 'user'
    openid = db.Column(db.String(40), primary_key=True)
    nickname = db.Column(db.String(20))
    head_img = db.Column(db.String(200))
    label = db.Column(db.String(50))
    reply_num = db.Column(db.Integer)
    type = db.Column(db.String(20))


class Zan(db.Model, Father):
    __tablename__ = 'zan'
    id = db.Column(db.BigInteger, primary_key=True)
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'))
    author_id = db.Column(db.String(40), db.ForeignKey('user.openid'))
    status = db.Column(db.SmallInteger)


class ZanComment(db.Model, Father):
    __tablename__ = 'zan_comment'
    id = db.Column(db.BigInteger, primary_key=True)
    comment_id = db.Column(db.BigInteger, db.ForeignKey('comment.id'))
    author_id = db.Column(db.String(40), db.ForeignKey('user.openid'))
    status = db.Column(db.SmallInteger)


class Reply(db.Model, Father):
    __tablename__ = 'reply'
    id = db.Column(db.BigInteger, primary_key=True)
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'))
    target_id = db.Column(db.String(40), db.ForeignKey('user.openid'))
    comment_id = db.Column(db.BigInteger, db.ForeignKey('comment.id'))
    sec_comment_id = db.Column(db.BigInteger, db.ForeignKey('comment_second.id'))
    verify_content = db.Column(db.String(50))
    is_read = db.Column(db.Boolean)


class UserVerify(db.Model, Father):
    __tablename__ = 'user_verify'
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(40), db.ForeignKey('user.openid'))
    content = db.Column(db.String(280))
    picture = db.Column(db.String(200))
    time = db.Column(db.DateTime)
    user_type = db.Column(db.String(20))


class Admin(db.Model, Father):
    __tablename__ = 'verify_admin'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    pwd = db.Column(db.String(20))

