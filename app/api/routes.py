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
        # Ottieni tutti i valori dalla POST request
        userName = request.form.get("UserName")
        pwd = request.form.get("Pwd")
        pwdRepeat = request.form.get("PwdRepeat")

        # Controlla che nessuno dei valori di input sia vuoto
        if api_functions.empty_input(userName, pwd, pwdRepeat):
            return jsonify(description="Empty input."), 400

        # Controlla che il nome sia valido
        if api_functions.invalid_name(userName):
            return jsonify(description="Invalid name."), 400

        # Controlla che le password siano uguali
        if pwd != pwdRepeat:
            return jsonify(description="Password don't match."), 400

        # Controlla che non ci siano già utenti con lo stesso nome
        if api_functions.get_name(MAINDB, userName):
            return jsonify(description="Username already in use."), 400

        # Genera un nuovo salt e poi prova a creare un nuovo account
        salt = uuid().hex
        if not api_functions.create_user(MAINDB, userName, pwd, salt):
            return (
                jsonify(
                    description="User creation failed.",
                    info="Error at: app/api/routes@sign_in()",
                ),
                500,
            )

        # Prova a loggare l'utente nell'account appena creato
        if api_functions.login_user(MAINDB, userName, pwd):
            return jsonify(description="Sign-in successful."), 200
        return (
            jsonify(
                description="Login failed.", info="Error at: app/api/routes@sign_in()"
            ),
            500,
        )
    except Exception as e:
        return (
            jsonify(
                description=f"An exception has occured: {e}",
                info="Error at: app/api/routes@sign_in()",
            ),
            500,
        )


@api.route("/login", methods=["POST"])
def login():
    try:
        # Controlla che la richiesta venga da una fonte confermata
        if request.form.get("Token") == session["Token"]:
            # Ottieni tutti i valori dalla POST request
            userName = request.form.get("UserName")
            pwd = request.form.get("Pwd")

            # Controlla che nessuno dei valori di input sia vuoto
            if api_functions.empty_input(userName, pwd):
                return jsonify(description="Empty input."), 400

            # Controlla che il nome sia valido
            if api_functions.invalid_name(userName):
                return jsonify(description="Invalid name."), 400

            # Controlla che l'utente esista e prendine la password e il salt
            res = api_functions.get_name(MAINDB, userName)
            if res:
                pwdHashed = res["Pwd"]
                salt = res["Salt"]
            else:
                return jsonify(description="User does not exist."), 400

            # Verifica che le password corrispondono
            if not api_functions.verify_password(pwd, salt, pwdHashed):
                return jsonify(description="Wrong Login."), 400

            # Prova a loggare l'utente
            if api_functions.login_user(MAINDB, userName, pwd):
                return jsonify(description="Login successful."), 200
            return (
                jsonify(
                    description="Login failed.", info="Error at: app/api/routes@login()"
                ),
                500,
            )
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return (
            jsonify(
                description=f"An exception has occured: {e}",
                info="Error at: app/api/routes@login()",
            ),
            500,
        )


@api.route("/logout/", methods=["POST"])
def logout():
    session.clear()
    return jsonify(description="Logout successful."), 200


@api.route("/create-campaign", methods=["POST"])
def create_campaign():
    try:
        if request.form.get("Token") == session["Token"]:
            name = request.form.get("Name")
            code = uuid().hex
            if (
                functions.SQL_query(
                    MAINDB,
                    "INSERT INTO Campaigns (Code, CampaignName, DungeonMaster) VALUES (%s, %s, %s);",
                    (code, name, session["Id"]),
                )
                == False
            ):
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@create_campaign() #1 SQL query",
                    ),
                    500,
                )

            CampaignDb = functions.create_db(
                config.DB_HOST_NAME,
                config.DB_HOST_PORT,
                config.DB_USER_NAME,
                config.DB_USER_PASSWORD,
                f"dnd_site_campaign_{code}",
            )
            if CampaignDb == False:
                return (
                    jsonify(
                        description="Database connection faliure (CampaignDb).",
                        info="Error at: app/api/routes@create_campaign() #1 database connection",
                    ),
                    500,
                )

            if (
                functions.SQL_query(
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
                )
                == False
            ):
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@create_campaign() #2 SQL query",
                    ),
                    500,
                )

            user = api_functions.get_name(MAINDB, session["UserName"])
            if user:
                campaigns = json.loads(user["Campaigns"])
                campaigns.append(
                    {"href": url_for("campaign", code=code), "code": code, "name": name}
                )
                if (
                    functions.SQL_query(
                        MAINDB,
                        "UPDATE Users SET Campaigns = %s WHERE id = %s;",
                        (
                            json.dumps(campaigns),
                            session["Id"],
                        ),
                    )
                    == False
                ):
                    return (
                        jsonify(
                            description="SQL query faliure.",
                            info="Error at: app/api/routes@create_campaign() #3 SQL query",
                        ),
                        500,
                    )

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
        return (
            jsonify(
                description=f"An exception has occured: {e}",
                info="Error at: app/api/routes@create_campaign()",
            ),
            500,
        )


@api.route("/delete-campaign", methods=["POST"])
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
            if CampaignDb == False:
                return (
                    jsonify(
                        description="Database connection faliure (CampaignDb).",
                        info="Error at: app/api/routes@delete_campaign() #1 database connection",
                    ),
                    500,
                )

            players = functions.SQL_query(CampaignDb, "SELECT * FROM Players;")
            if players == False:
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@delete_campaign() #1 SQL query",
                    ),
                    500,
                )
            for player in players:
                player_data = functions.SQL_query(
                    MAINDB,
                    "SELECT * FROM Users WHERE Id=%s;",
                    (player["Id"],),
                    single=True,
                )
                if player_data == False:
                    return (
                        jsonify(
                            description="SQL query faliure.",
                            info="Error at: app/api/routes@delete_campaign() #2 SQL query",
                        ),
                        500,
                    )
                campaigns = json.loads(player_data["Campaigns"])
                for c in campaigns:
                    if c["code"] == code:
                        campaigns.remove(c)
                if (
                    functions.SQL_query(
                        MAINDB,
                        "UPDATE Users SET Campaigns=%s WHERE Id=%s;",
                        (json.dumps(campaigns), player["Id"]),
                    )
                    == False
                ):
                    return (
                        jsonify(
                            description="SQL query faliure.",
                            info="Error at: app/api/routes@delete_campaign() #3 SQL query",
                        ),
                        500,
                    )

            dm_id = functions.SQL_query(
                MAINDB, "SELECT * FROM Campaigns WHERE Code=%s;", (code,), single=True
            )
            if dm_id == False:
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@delete_campaign() #4 SQL query",
                    ),
                    500,
                )
            dm_id = int(dm_id["DungeonMaster"])
            dm = functions.SQL_query(
                MAINDB, "SELECT * FROM Users WHERE Id=%s;", (dm_id,), single=True
            )
            if dm == False:
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@delete_campaign() #5 SQL query",
                    ),
                    500,
                )
            campaigns = json.loads(dm["Campaigns"])
            for c in campaigns:
                if c["code"] == code:
                    campaigns.remove(c)

            if (
                functions.SQL_query(
                    MAINDB,
                    "UPDATE Users SET Campaigns=%s WHERE Id=%s;",
                    (json.dumps(campaigns), dm_id),
                )
                == False
            ):
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@delete_campaign() #6 SQL query",
                    ),
                    500,
                )

            if (
                functions.SQL_query(
                    CampaignDb, "DROP DATABASE %s;", (f"dnd_site_campaign_{code}",)
                )
                == False
            ):
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@delete_campaign() #7 SQL query",
                    ),
                    500,
                )

            if (
                functions.SQL_query(
                    MAINDB,
                    "DELETE FROM Campaigns WHERE Code=%s;",
                    (code),
                )
                == False
            ):
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/api/routes@delete_campaign() #8 SQL query",
                    ),
                    500,
                )

            return jsonify(description="Campagna rimossa."), 200
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return (
            jsonify(
                description=f"An exception has occured: {e}",
                info="Error at: app/api/routes@delete_campaign()",
            ),
            500,
        )
