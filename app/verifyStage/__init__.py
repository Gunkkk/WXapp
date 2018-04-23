from flask import Blueprint

verify = Blueprint("verify", __name__, template_folder='templates')

from app.verifyStage import api