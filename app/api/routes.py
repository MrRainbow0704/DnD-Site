from flask import request, session, url_for
from uuid import uuid4 as uuid
import json
from . import api_functions
from . import bp as api
from .. import DbHostName, DbUserName, DbUserPassword, MainDb, functions


@api.route("/sign-in", methods=["POST"])
def sign_in():
    if request.method == "POST":
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        pwdRepeat = request.form.get("PwdRepeat")
        if api_functions.empty_input(userName, pwd, pwdRepeat):
            return {"code": 401, "status": "Empty input."}
        if api_functions.invalid_name(userName):
            return {"code": 401, "status": "Invalid name."}
        if pwd != pwdRepeat:
            return {"code": 401, "status": "Password don't match."}
        if api_functions.get_name(MainDb, userName) != False:
            return {"code": 401, "status": "Username already in use."}
        api_functions.create_user(MainDb, userName, pwd)
        if api_functions.login_user(MainDb, userName, pwd):
            return {"code": 200, "status": "OK, Sign-in successful."}
        else:
            return {"code": 401, "status": "Wrong Login."}


@api.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        if api_functions.empty_input(userName, pwd):
            return {"code": 401, "status": "Empty input."}
        if api_functions.invalid_name(userName):
            return {"code": 401, "status": "Invalid name."}
        res = api_functions.get_name(MainDb, userName)
        if res:
            pwdHashed = res["Pwd"]
        else:
            return {"code": 401, "status": "User does not exist."}
        if not api_functions.verify_password(pwd, pwdHashed):
            return {"code": 401, "status": "Wrong Login."}
        success = api_functions.login_user(MainDb, userName, pwd)
        if success:
            return {"code": 200, "status": "OK, Login successful."}
        return {"code": 401, "status": "Login failed."}


@api.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return {"code": 200, "status": "OK, Logout successful."}


@api.route("/create-campaign", methods=["POST"])
def create_campaign():
    name = request.form.get("Name")
    code = uuid().hex
    functions.SQL_query(
        MainDb,
        "INSERT INTO Campaigns (Code, DungeonMaster) VALUES (?, ?);",
        (code, session["Id"]),
    )
    CampaignDb = functions.create_db(
        DbHostName, DbUserName, DbUserPassword, f"dnd_site_campaign_{code}"
    )
    functions.SQL_query(
        CampaignDb,
        """CREATE TABLE IF NOT EXISTS Players (
            UserId INTEGER PRIMARY KEY,
            Name TEXT UNIQUE NOT NULL,
            Dmg INTEGER DEFAULT 0,
            BaseHp INTEGER DEFAULT 0,
            Ap INTEGER DEFAULT 0,
            Lvl INTEGER DEFAULT 1,
            Exp INTEGER DEFAULT 0,
            MaxHp INTEGER DEFAULT 0,
            Inventory TEXT DEFAULT '[]',
            Class TEXT DEFAULT '{}',
            Race TEXT DEFAULT '{}',
            Equipment TEXT DEFAULT '{}',
            Stats TEXT DEFAULT '{}'
            );
            """,
    )
    user = api_functions.get_name(MainDb, session["UserName"])
    if user:
        campaigns = json.loads(user["Campaigns"])
        campaigns.append({"href": url_for("campaign", code=code), "name": name})
        functions.SQL_query(MainDb, "INSERT INTO Users Campaigns VALUES ?;")
    return {"code": 200, "status": url_for("campagna", code=code)}
