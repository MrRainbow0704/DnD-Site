from flask import request, session
from . import functions
from . import bp as api
from .. import UsersDb


@api.route("/sign-in", methods=["POST"])
def sign_in():
    if request.method == "POST":
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        pwdRepeat = request.form.get("PwdRepeat")
        if functions.empty_input(userName, pwd, pwdRepeat):
            return {"code": 401, "status": "Empty input."}
        if functions.invalid_name(userName):
            return {"code": 401, "status": "Invalid name."}
        if pwd != pwdRepeat:
            return {"code": 401, "status": "Password don't match."}
        if functions.get_name(UsersDb, userName) != False:
            return {"code": 401, "status": "Username already in use."}
        functions.create_user(UsersDb, userName, pwd)
        if functions.login_user(UsersDb, userName, pwd):
            return {"code": 200, "status": "OK, Sign-in successful."}
        else:
            return {"code": 401, "status": "Wrong Login."}


@api.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        if functions.empty_input(userName, pwd):
            return {"code": 401, "status": "Empty input."}
        if functions.invalid_name(userName):
            return {"code": 401, "status": "Invalid name."}
        res = functions.get_name(UsersDb, userName)
        if res:
            pwdHashed = res["Pwd"]
        else:
            return {"code": 401, "status": "User does not exist."}
        if not functions.verify_password(pwd, pwdHashed):
            return {"code": 401, "status": "Wrong Login."}
        success = functions.login_user(UsersDb, userName, pwd)
        if success:
            return {"code": 200, "status": "OK, Login successful."}
        return {"code": 401, "status": "Login failed."}


@api.route("/logout")
def logout():
    session.clear()
    return {"code": 200, "status": "OK, Logout successful."}
