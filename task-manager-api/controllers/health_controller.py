from flask import jsonify

from utils.constants import API_NAME, API_VERSION
from utils.dates import utcnow


def index():
    return jsonify({"message": API_NAME, "version": API_VERSION}), 200


def health():
    return jsonify({"status": "ok", "timestamp": str(utcnow())}), 200
