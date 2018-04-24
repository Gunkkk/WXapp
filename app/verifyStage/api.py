from . import verify
from app import db
from app.model import UserVerify, Admin, User
from flask import render_template, request, redirect, url_for, jsonify, session
from app.verifyStage.task import *
'''
17 userTypeVerify
18 adminLogin
19 getUserVerify
20 verifyComplete
'''


@verify.route('/index/')
def user_type_verify():
    return render_template('/html/adminLogin.html')


@verify.route('/adminLogin/', methods=['post', 'get'])
def admin_login():
    name = request.form.get('name')
    pwd = request.form.get('pwd')

    msg = ''
    admin = Admin.query.filter_by(name=name).first()
    if admin is None:
        msg = 'name error!'
    elif admin.pwd != pwd:
        msg = 'password error!'
    else:
        session['username'] = name
        return redirect(url_for('verify.get_user_verify'))

    return render_template('/html/adminLogin.html', msg=msg)


@verify.route('/getUserVerify/', methods=['post', 'get'])
def get_user_verify():
    if 'username' not in session:
        return render_template('/html/adminLogin.html')
    list = UserVerify.query.all()
    temp = []
    for i in list:
        i = i.get_dict()
        temp.append(i)
    return render_template('/html/verify.html', list=temp)


@verify.route('/verifyComplete/<id>/<flag>/<type>/<verify_content>')
def verify_complete(id, flag, type, verify_content):
    verify = UserVerify.query.filter_by(id=id).first()
    if verify is None:
        return 'wrong id'
    openid = verify.openid
    if flag == '通过':
        user = User.query.filter_by(openid=openid).first()
        if user is None:
            return 'wrong openid'
        user.type = type
        db.session.add(user)
    get_verify_reply.delay(openid, verify_content)
    db.session.delete(verify)
    db.session.commit()
    return 'success'
