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
    score = db.Column(db.Integer)
    time = db.Column(db.DateTime)
    anonymous = db.Column(db.Boolean)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    overall_score = db.Column(db.Float)


class Comment(db.Model, Father):
    __tablename__ = 'comment'
    id = db.Column(db.BigInteger, primary_key=True)
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'))
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
    head_img = db.Column(db.String(50))
    label = db.Column(db.String(50))


class Zan(db.Model,Father):
    __tablename__ = 'zan'
    id = db.Column(db.BigInteger, primary_key=True)
    msg_id = db.Column(db.BigInteger, db.ForeignKey('msg.id'))
    author_id = db.Column(db.String(40), db.ForeignKey('user.openid'))
    status = db.Column(db.Boolean)  # 1√ 0×


