from flask import request, url_for, session, Response
from . import functions
from . import bp as api
from .. import UserDb


@api.route("/")
def index():
    from flask import Flask
    temp_app = Flask(__name__) 
    temp_app.register_blueprint(api)
    html = [f"<a href='.{str(p)}'>{str(p)}</a>" if str(p).count("<") == 0 else f"<a href='#'>{str(p)}</a>" for p in temp_app.url_map.iter_rules()]
    return "<br>".join(html)

@api.route("/sign-in")
def sign_in():
    userName = request.args.get("UserName")
    pwd = request.args.get("Pwd")
    pwdRepeat = request.args.get("PwdRepeat")
    if functions.empty_input(userName, pwd, pwdRepeat):
        return {"code": 401, "status": "Unauthorized, Sign-in failed."}
    if functions.invalid_name(userName):
        return {"code": 401, "status": "Unauthorized, Sign-in failed."}
    if pwd != pwdRepeat:
        return {"code": 401, "status": "Unauthorized, Sign-in failed."}
    pwdHashed = functions.hash_password(pwd)
    functions.create_user(UserDb, userName, pwdHashed)
    functions.login_user(UserDb, userName, pwd)
    return {"code": 200, "status": "OK, Sign-in successful."}


@api.route("/login")
def login():
    userName = request.args.get("UserName")
    pwd = request.args.get("Pwd")
    if functions.empty_input(userName, pwd):
        return {"code": 401, "status": "Unauthorized, Login failed."}
    if functions.invalid_name(userName):
        return {"code": 401, "status": "Unauthorized, Login failed."}
    res = functions.get_name(UserDb, userName)
    if res:
        pwdHashed = res["Pwd"]
    if not functions.verify_password(pwd, pwdHashed):
        return {"code": 401, "status": "Unauthorized, Login failed."}
    success = functions.login_user(UserDb, userName, pwd)
    if success:
        return {"code": 200, "status": "OK, Login successful."}
    return {"code": 401, "status": "Unauthorized, Login failed."}


@api.route("/logout")
@functions.login_required
def logout():
    session.clear()
    return {"code": 200, "status": "OK, Logout successful."}
