from flask import request, url_for, session, redirect
from . import functions
from . import bp as api
from .. import UsersDb


@api.route("/")
def index():
    from flask import Flask

    temp_app = Flask(__name__)
    temp_app.register_blueprint(api)
    html = [
        f"<a href='.{str(p)}'>{str(p)}</a>"
        if str(p).count("<") == 0
        else f"<a href='#'>{str(p)}</a>"
        for p in temp_app.url_map.iter_rules()
    ]
    return "<br>".join(html)


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
        pwdHashed = functions.hash_password(pwd)
        functions.create_user(UsersDb, userName, pwdHashed)
        functions.login_user(UsersDb, userName, pwd)
        return {"code": 200, "status": "OK, Sign-in successful."}


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
        if not functions.verify_password(pwd, pwdHashed):
            return {"code": 401, "status": "Wrong Login."}
        success = functions.login_user(UsersDb, userName, pwd)
        if success:
            return {"code": 200, "status": "OK, Login successful."}
        return {"code": 401, "status": "Login failed."}


@api.route("/logout")
def logout():
    if "LoggedIn" in session and session["LoggedIn"]:
        pass
    else:
        return redirect(url_for('sign_in'))
    session.clear()
    return {"code": 200, "status": "OK, Logout successful."}
