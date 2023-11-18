from flask import request, session, url_for
from uuid import uuid4 as uuid
import json
from . import api_functions
from . import bp as api
from .. import DBHOSTNAME, DBUSERNAME, DBUSERPASSWORD, MAINDB, functions


@api.route("/sign-in", methods=["POST"])
def sign_in():
    if request.form.get("Token") == request["Token"]:
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        pwdRepeat = request.form.get("PwdRepeat")
        if api_functions.empty_input(userName, pwd, pwdRepeat):
            return {"code": 401, "status": "Empty input."}
        if api_functions.invalid_name(userName):
            return {"code": 401, "status": "Invalid name."}
        if pwd != pwdRepeat:
            return {"code": 401, "status": "Password don't match."}
        if api_functions.get_name(MAINDB, userName) != False:
            return {"code": 401, "status": "Username already in use."}
        api_functions.create_user(MAINDB, userName, pwd)
        if api_functions.login_user(MAINDB, userName, pwd):
            return {"code": 200, "status": "OK, Sign-in successful."}
        else:
            return {"code": 401, "status": "Wrong Login."}
    else:
        return {"code": 401, "status": "Token non valido."}


@api.route("/login", methods=["POST"])
def login():
    if request.form.get("Token") == request["Token"]:
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        if api_functions.empty_input(userName, pwd):
            return {"code": 401, "status": "Empty input."}
        if api_functions.invalid_name(userName):
            return {"code": 401, "status": "Invalid name."}
        res = api_functions.get_name(MAINDB, userName)
        if res:
            pwdHashed = res["Pwd"]
        else:
            return {"code": 401, "status": "User does not exist."}
        if not api_functions.verify_password(pwd, pwdHashed):
            return {"code": 401, "status": "Wrong Login."}
        success = api_functions.login_user(MAINDB, userName, pwd)
        if success:
            return {"code": 200, "status": "OK, Login successful."}
        return {"code": 401, "status": "Login failed."}
    else:
        return {"code": 401, "status": "Token non valido."}


@api.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return {"code": 200, "status": "OK, Logout successful."}



@api.route("/create-campaign", methods=["POST"])
def create_campaign():
    if request.form.get("Token") == request["Token"]:
        name = request.form.get("Name")
        code = uuid().hex
        functions.SQL_query(
            MAINDB,
            "INSERT INTO Campaigns (Code, CampaignName, DungeonMaster) VALUES (%s, %s, %s);",
            (code, name, session["Id"]),
        )
        CampaignDb = functions.create_db(
            DBHOSTNAME, DBUSERNAME, DBUSERPASSWORD, f"dnd_site_campaign_{code}"
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
        user = api_functions.get_name(MAINDB, session["UserName"])
        if user:
            campaigns = json.loads(user["Campaigns"])
            campaigns.append(
                {"href": url_for("campaign", code=code), "code": code, "name": name}
            )
            functions.SQL_query(
                MAINDB,
                "UPDATE Users SET Campaigns = %s WHERE id = %s;",
                (
                    json.dumps(campaigns),
                    session["Id"],
                ),
            )
        return {
            "code": 200,
            "status": "Creazione completata",
            "redirect": url_for("campaign", code=code),
        }
    else:
        return {"code": 401, "status": "Token non valido."}


@api.route("delete-campaign", methods=["POST"])
def delete_campaign():
    if request.form.get("Token") == request["Token"]:
        code = request.form.get("Code")
        CampaignDb = functions.db_connect(
            DBHOSTNAME, DBUSERNAME, DBUSERPASSWORD, f"dnd_site_campaign_{code}"
        )
        # TODO espellere ogni player quando rimuovo la campagna
        dm_id = functions.SQL_query(
            MAINDB, "SELECT * FROM Campaigns WHERE code=%s;", (code,), single=True
        )["DungeonMaster"]
        dm = functions.SQL_query(
            MAINDB, "SELECT * FROM Users WHERE Id=%s;", (dm_id,), single=True
        )
        campaigns = json.loads(dm["Campaigns"])
        for c in campaigns:
            if c["code"] == code:
                campaigns.remove(c)
        functions.SQL_query(
            MAINDB, "UPDATE Users SET Campaigns=%s;", (json.dumps(campaigns),)
        )
        functions.SQL_query(
            CampaignDb, "DROP DATABASE %s;", (f"dnd_site_campaign_{code}",)
        )
        functions.SQL_query(
            MAINDB,
            "DELETE FROM Campaigns WHERE Code=%s;",
            (code),
        )
        return {"code": 200, "status": "Campagna rimossa."}
    else:
        return {"code": 401, "status": "Token non valido."}
