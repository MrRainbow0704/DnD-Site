from flask import request, url_for
from . import bp


@bp.route("/login")
def login():
    return {}