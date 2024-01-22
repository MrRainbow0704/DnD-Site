"""Un modulo con tutte le direttive per gli url dell'API"""

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
        if functions.get_user_from_name(MAINDB, userName):
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
                description=f"An exception has occurred: {e}",
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
            res = functions.get_user_from_name(MAINDB, userName)
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
                description=f"An exception has occurred: {e}",
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
            if api_functions.empty_input(name):
                return jsonify(description="Empty input."), 400
            
            code = api_functions.create_campaign(MAINDB, name, session["Id"])
            if code == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@create_campaign() #1 SQL query",
                    ),
                    500,
                )
            if api_functions.add_campaign(MAINDB, code, name, session["Id"]) == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@create_campaign() #2 SQL query",
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
                description=f"An exception has occurred: {e}",
                info="Error at: app/api/routes@create_campaign()",
            ),
            500,
        )


@api.route("/delete-campaign", methods=["POST"])
def delete_campaign():
    try:
        if request.form.get("Token") == session["Token"]:
            code = request.form.get("Code")
            if api_functions.empty_input(code):
                return jsonify(description="Empty input."), 400

            players = api_functions.get_campaign_players(MAINDB, code)
            if players == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@delete_campaign() #1 SQL query",
                    ),
                    500,
                )
            for player in players:
                if api_functions.remove_campaign(MAINDB, code, player["UserId"]) == False:
                    return (
                        jsonify(
                            description="SQL query failure.",
                            info="Error at: app/api/routes@delete_campaign() #2 SQL query",
                        ),
                        500,
                    )

            dm_id = api_functions.get_dm_id(MAINDB, code)
            if dm_id == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@delete_campaign() #3 SQL query",
                    ),
                    500,
                )

            if api_functions.remove_campaign(MAINDB, code, dm_id) == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@delete_campaign() #4 SQL query",
                    ),
                    500,
                )

            if api_functions.delete_campaign(MAINDB, code) == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@delete_campaign() #5 SQL query",
                    ),
                    500,
                )

            return (
                jsonify(
                    description="Campagna rimossa.",
                    redirect=url_for("profile"),
                ),
                200,
            )
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        # return (
        #     jsonify(
        #         description=f"An exception has occurred: {e}",
        #         info="Error at: app/api/routes@delete_campaign()",
        #     ),
        #     500,
        # )
        raise e


@api.route("/join_campaign", methods=["POST"])
def join_campaign():
    try:
        if request.form.get("Token") == session["Token"]:
            code = request.form.get("Code")
            name = request.form.get("Name")
            if api_functions.empty_input(code, name):
                return jsonify(description="Empty input."), 400

            if api_functions.join_campaign(MAINDB, code, session["Id"], name) == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@join_campaign() #1 SQL query",
                    ),
                    500,
                )
            return (
                jsonify(
                    description="Ti sei unito alla campagna.",
                    redirect=url_for("campaign", code=code),
                ),
                200,
            )
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return (
            jsonify(
                description=f"An exception has occurred: {e}",
                info="Error at: app/api/routes@join_campaign()",
            ),
            500,
        )


@api.route("/leave_campaign", methods=["POST"])
def leave_campaign():
    try:
        if request.form.get("Token") == session["Token"]:
            code = request.form.get("Code")
            name = request.form.get("Name")
            if api_functions.empty_input(code, name):
                return jsonify(description="Empty input."), 400
            
            user = functions.get_user_from_name(MAINDB, name)
            if user == False:
                return (
                    jsonify(
                        description="Database connection failure (MainDb).",
                        info="Error at: app/api/routes@leave_campaign() #1 database connection",
                    ),
                    500,
                )
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
                        description="Database connection failure (CampaignDb).",
                        info="Error at: app/api/routes@leave_campaign() #2 database connection",
                    ),
                    500,
                )

            if (
                functions.SQL_query(
                    CampaignDb,
                    "DELETE * FROM Players WHERE UserId = %s;",
                    (user["Id"],),
                )
                == False
            ):
                return jsonify(
                    description="SQL query failure.",
                    info="Error at: app/api/routes@leave_campaign() #1 SQL query",
                )

            player_data = functions.SQL_query(
                MAINDB,
                "SELECT * FROM Users WHERE Id=%s;",
                (session["Id"],),
                single=True,
            )
            if player_data == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@leave_campaign() #2 SQL query",
                    ),
                    500,
                )
            campaign = functions.SQL_query(
                MAINDB,
                "SELECT * FROM Campaigns WHERE Code=%s;",
                (code,),
                single=True,
            )
            if campaign == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@leave_campaign() #3 SQL query",
                    ),
                    500,
                )
            campaign_players = json.loads(campaign["Players"])
            campaign_players.remove(session["Id"])
            if (
                functions.SQL_query(
                    MAINDB,
                    "UPDATE Campaigns SET Players=%s WHERE Code=%s;",
                    (json.dumps(campaign_players), code),
                )
                == False
            ):
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@leave_campaign() #4 SQL query",
                    ),
                    500,
                )
            campaigns = json.loads(player_data["Campaigns"])
            for campaign in campaigns:
                if campaign["code"] == code:
                    campaigns.remove(campaign)
                    break
            if (
                functions.SQL_query(
                    MAINDB,
                    "UPDATE Users SET Campaigns=%s WHERE Id=%s;",
                    (json.dumps(campaigns), session["Id"]),
                )
                == False
            ):
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/api/routes@leave_campaign() #5 SQL query",
                    ),
                    500,
                )
            return (
                jsonify(
                    description="Hai abbandonato campagna.",
                    redirect=url_for("profile"),
                ),
                200,
            )
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return (
            jsonify(
                description=f"An exception has occurred: {e}",
                info="Error at: app/api/routes@leave_campaign()",
            ),
            500,
        )


@api.route("/upload-docs", methods=["POST"])
def upload_docs():
    try:
        if request.form.get("Token") == session["Token"]:
            file = request.form.get("markdown")
            with open(config.UPLOADS_PATH / "file.md", "w") as f:
                # Non so perché vada diviso in lista ma se lo faccio senza si rompe
                f.writelines(file.split("\n"))
            return (
                jsonify(
                    description="Hai abbandonato campagna.",
                    redirect=url_for("documentation"),
                ),
                200,
            )
        else:
            return jsonify(description="Token non valido."), 403
    except Exception as e:
        return (
            jsonify(
                description=f"An exception has occurred: {e}",
                info="Error at: app/api/routes@upload()",
            ),
            500,
        )
