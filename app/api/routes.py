from flask import request, session, url_for, jsonify
from uuid import uuid4 as uuid
import json
import config
from . import api_functions
from . import bp as api
from .. import MAINDB, functions


@api.route("/sign-in", methods=["POST"])
def sign_in():
    try:
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        pwdRepeat = request.form.get("PwdRepeat")

        if api_functions.empty_input(userName, pwd, pwdRepeat):
            return jsonify(description="Empty input."), 400

        if api_functions.invalid_name(userName):
            return jsonify(description="Invalid name."), 400

        if pwd != pwdRepeat:
            return jsonify(description="Password don't match."), 400

        if api_functions.get_name(MAINDB, userName):
            return jsonify(description="Username already in use."), 400

        salt = uuid().hex
        api_functions.create_user(MAINDB, userName, pwd, salt)
        if api_functions.login_user(MAINDB, userName, pwd):
            return jsonify(description="Sign-in successful."), 200
        else:
            return jsonify(description="Login failed."), 500
    except Exception as e:
        return jsonify(description=f"An exception has occured: {e}"), 500


@api.route("/login", methods=["POST"])
def login():
    try:
        if request.form.get("Token") == session["Token"]:
            userName = request.form.get("UserName")
            pwd = request.form.get("Pwd")
            if api_functions.empty_input(userName, pwd):
                return jsonify(description="Empty input."), 400

            if api_functions.invalid_name(userName):
                return jsonify(description="Invalid name."), 400

            res = api_functions.get_name(MAINDB, userName)
            if res:
                pwdHashed = res["Pwd"]
                salt = res["Salt"]
            else:
                return jsonify(description="User does not exist."), 400

            if not api_functions.verify_password(pwd, salt, pwdHashed):
                return jsonify(description="Wrong Login."), 400

            if api_functions.login_user(MAINDB, userName, pwd):
                return jsonify(description="Login successful."), 200
            return jsonify(description="Login failed."), 500
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return jsonify(description=f"An exception has occured: {e}"), 500


@api.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(description="Logout successful."), 200


@api.route("/create-campaign", methods=["POST"])
def create_campaign():
    try:
        if request.form.get("Token") == session["Token"]:
            name = request.form.get("Name")
            code = uuid().hex
            if not functions.SQL_query(
                MAINDB,
                "INSERT INTO Campaigns (Code, CampaignName, DungeonMaster) VALUES (%s, %s, %s);",
                (code, name, session["Id"]),
            ):
                return jsonify(description="SQL query faliure."), 500

            CampaignDb = functions.create_db(
                config.DB_HOST_NAME,
                config.DB_HOST_PORT,
                config.DB_USER_NAME,
                config.DB_USER_PASSWORD,
                f"dnd_site_campaign_{code}",
            )
            if not CampaignDb:
                return (
                    jsonify(description="Database connection faliure (CampaignDb)."),
                    500,
                )

            if not functions.SQL_query(
                CampaignDb,
                """CREATE TABLE IF NOT EXISTS Players (
                    UserId INTEGER PRIMARY KEY,
                    Name TEXT UNIQUE NOT NULL,
                    Dmg INTEGER DEFAULT 0,
                    BaseHp INTEGER  DEFAULT 0,
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
            ):
                return jsonify(description="SQL query faliure."), 500

            user = api_functions.get_name(MAINDB, session["UserName"])
            if user:
                campaigns = json.loads(user["Campaigns"])
                campaigns.append(
                    {"href": url_for("campaign", code=code), "code": code, "name": name}
                )
                if not functions.SQL_query(
                    MAINDB,
                    "UPDATE Users SET Campaigns = %s WHERE id = %s;",
                    (
                        json.dumps(campaigns),
                        session["Id"],
                    ),
                ):
                    return jsonify(description="SQL query faliure."), 500

            return (
                jsonify(
                    description="Creazione completata",
                    redirect=url_for("campaign", code=code),
                ),
                200,
            )
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return jsonify(description=f"An exception has occured: {e}"), 500


@api.route("delete-campaign", methods=["POST"])
def delete_campaign():
    try:
        if request.form.get("Token") == session["Token"]:
            code = request.form.get("Code")
            CampaignDb = functions.db_connect(
                config.DB_HOST_NAME,
                config.DB_HOST_PORT,
                config.DB_USER_NAME,
                config.DB_USER_PASSWORD,
                f"dnd_site_campaign_{code}",
            )
            if not CampaignDb:
                return jsonify(description="Database connection faliure (CampaignDb)."), 500

            # TODO espellere ogni player quando rimuovo la campagna
            dm_id = functions.SQL_query(
                MAINDB, "SELECT * FROM Campaigns WHERE Code=%s;", (code,), single=True
            )
            if not dm_id:
                return jsonify(description="SQL query faliure."), 500
            dm_id = dm_id["DungeonMaster"]
            dm = functions.SQL_query(
                MAINDB, "SELECT * FROM Users WHERE Id=%s;", (dm_id,), single=True
            )
            if not dm:
                return jsonify(description="SQL query faliure."), 500
            players_id = functions.SQL_query(
                MAINDB, "SELECT * FROM CAmpaigns WHERE Code=%s;", (code,)
            )
            if not players_id:
                return jsonify(description="SQL query faliure."), 500
            campaigns = json.loads(dm["Campaigns"])
            for c in campaigns:
                if c["code"] == code:
                    campaigns.remove(c)

            if not functions.SQL_query(
                MAINDB, "UPDATE Users SET Campaigns=%s;", (json.dumps(campaigns),)
            ):
                return jsonify(description="SQL query faliure."), 500

            if not functions.SQL_query(
                CampaignDb, "DROP DATABASE %s;", (f"dnd_site_campaign_{code}",)
            ):
                return jsonify(description="SQL query faliure."), 500

            if not functions.SQL_query(
                MAINDB,
                "DELETE FROM Campaigns WHERE Code=%s;",
                (code),
            ):
                return jsonify(description="SQL query faliure."), 500

            return jsonify(description="Campagna rimossa."), 200
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return jsonify(description=f"An exception has occured: {e}"), 500
