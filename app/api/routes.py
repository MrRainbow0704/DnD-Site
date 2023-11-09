from flask import request, url_for, session, Response
from . import functions
from . import bp as api
from .. import UserDb


@api.route("/sign-in")
def sign_in():
    userName = request["UserName"]
    pwd = request["Pwd"]
    pwdRepeat = request["PwdRepeat"]
    if functions.invalid_name(userName):
        return {"code": 401, "status": "Unauthorized, Login failed."}
    if functions.empty_input(userName, pwd, pwdRepeat):
        return {"code": 401, "status": "Unauthorized, Login failed."}
    if pwd != pwdRepeat:
        return {"code": 401, "status": "Unauthorized, Login failed."}
    pwdHashed = functions.hash_password(pwd)
    functions.create_user(UserDb, userName, pwdHashed)
    functions.login_user(UserDb, userName, pwd)
    return {"code": 200, "status": "OK, Login successful."}


@api.route("/login")
def login():
    userName = request["UserName"]
    pwd = request["Pwd"]
    res = UserDb.query("SELECT * FROM Users WHERE UserName=?", (userName,))
    pwdHashed = res["Pwd"]
    if not functions.verify_password(pwd, pwdHashed):
        return {"code": 401, "status": "Unauthorized, Login failed."}
    success = functions.login_user(UserDb, userName, pwd)
    if success:
        return {"code": 200, "status": "OK, Login successful."}
    else:
        return {"code": 401, "status": "Unauthorized, Login failed."}


@api.route("/logout")
@functions.login_required
def logout():
    session.clear()
    return {"code": 200, "status": "OK, Logout successful."}
