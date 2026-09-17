from flask import jsonify

from errors import NotFoundError
from models.user import User
from services import report_service

MSG_USER_NOT_FOUND = "Usuário não encontrado"


def summary_report():
    return jsonify(report_service.summary()), 200


def user_report(user_id):
    user = User.get(user_id)
    if not user:
        raise NotFoundError(MSG_USER_NOT_FOUND)
    return jsonify(report_service.user_report(user)), 200
