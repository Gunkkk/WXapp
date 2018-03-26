from flask import Blueprint

msg = Blueprint("msg", __name__)

from app.msg import api
