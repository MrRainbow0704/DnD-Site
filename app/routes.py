"""Un modulo con tutte le direttive per gli url base"""

from flask import render_template, redirect, session, url_for, jsonify, request
import json
import config
from uuid import uuid4
from markdown import markdown
from .api import routes as api_routes
from .api import api_functions
from . import app, functions, MAINDB


@app.route("/")
def index():
    """Route per la pagina index"""

    # Aggiorna il token e renderizza la pagina
    session["Token"] = uuid4().hex
    return (
        render_template(
            "index.html",
            token=session["Token"],
        ),
        200,
    )


@app.route("/sign-in")
def sign_in():
    """Route per la pagina di registrazione"""

    # Aggiorna il token e renderizza la pagina
    session["Token"] = uuid4().hex
    return (
        render_template(
            "sign_in.html",
            token=session["Token"],
        ),
        200,
    )


@app.route("/login")
def login():
    """Route per la pagina di login"""

    # Aggiorna il token e renderizza la pagina
    session["Token"] = uuid4().hex
    return (
        render_template(
            "login.html",
            token=session["Token"],
        ),
        200,
    )


@app.route("/logout")
def logout():
    """Route per la pagina di logout"""

    # Aggiorna il token e renderizza la pagina
    if functions.is_logged_in():
        api_routes.logout()
        return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))


@app.route("/profilo")
def profile():
    """Route per la pagina profilo"""

    # Controlla che l'utente sia loggato altrimenti lo porta a login
    if functions.is_logged_in():
        # Aggiorna il token, prende le campagne a cui l'utente partecipa e renderizza la pagina
        session["Token"] = uuid4().hex
        res = functions.get_user_from_id(MAINDB, session["Id"])
        return (
            render_template(
                "profile.html",
                campagne=json.loads(res["Campaigns"]),
                token=session["Token"],
            ),
            200,
        )
    else:
        return redirect(url_for("login"))


# @app.route("/campagna/<string:code>/documentazione")
# def documentation(code: str):
#     """Route per la pagina documentazione"""
#     with open(config.UPLOADS_PATH / f"{code}.md", "r", encoding="UTF-8") as f:
#         text = f.read()
#     file = {"html": markdown(text, output_format="html"), "md": text}
#     # Aggiorna il token e renderizza la pagina
#     session["Token"] = uuid4().hex
#     return render_template("documentation.html", file=file, token=session["Token"]), 200
@app.route("/documentazione")
def documentation():
    return ""


@app.route("/campagna/<string:code>")
def campaign(code: str):
    """Route per la pagina campagna

    Args:
        code (str): Codice della campagna
    """

    # Controlla che l'utente sia loggato altrimenti lo porta a login
    if functions.is_logged_in():
        # Aggiorna il token, prende le campagne a cui l'utente partecipa
        session["Token"] = uuid4().hex
        campagne = functions.get_user_campaigns(MAINDB, session["Id"])
        if campagne == False:
            return (
                jsonify(
                    description="SQL query failure.",
                    info="Error at: app/routes@campaign() #1 SQL query",
                ),
                500,
            )
        # Controlla che l'utente sia un membro della campagna altrimenti lo porta a profilo

        campagne_id = [x["code"] for x in campagne]
        if code in campagne_id:
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
                        info="Error at: app/routes@campaign() #1 database connection",
                    ),
                    500,
                )

            campagna = functions.get_campaign_from_code(MAINDB, code)
            if campagna == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/routes@campaign() #2 SQL query",
                    ),
                    500,
                )

            # Controlla se l'utente è il Dungeon Master, altrimenti provvede al prelievo dei dati
            if campagna["DungeonMaster"] == session["Id"]:
                player = "DM"

            else:
                player = functions.get_player_from_id(CampaignDb, session["Id"])
                if player == False:
                    return (
                        jsonify(
                            description="SQL query failure.",
                            info="Error at: app/routes@campaign() #3 SQL query",
                        ),
                        500,
                    )
            players = []
            for pId in json.loads(campagna["Players"]):
                if type(pId) == int:
                    pl = functions.get_user_from_id(MAINDB, pId)
                else:
                    pl = functions.get_user_from_id(MAINDB, pId["Id"])
                if pl == False:
                    return (
                        jsonify(
                            description="SQL query failure.",
                            info="Error at: app/routes@join_campaign() #2 SQL query.",
                        ),
                        500,
                    )

                players.append(pl["UserName"])
            # Alla fine renderizza la pagina con tutte le sue variabili
            return (
                render_template(
                    "campaign.html",
                    campaign=campagna,
                    campagne=campagne,
                    player=player,
                    # players=players,
                    token=session["Token"],
                ),
                200,
            )
        else:
            return redirect(url_for("profile"))
    else:
        return redirect(url_for("login"))


@app.route("/unisciti/<string:code>")
def join_campaign(code: str):
    # Controlla che l'utente sia loggato
    if functions.is_logged_in():
        # Aggiorna il token, prende le campagne a cui l'utente partecipa
        session["Token"] = uuid4().hex
        campagne = functions.get_user_campaigns(MAINDB, session["Id"])
        if campagne == False:
            return (
                jsonify(
                    description="SQL query failure.",
                    info="Error at: app/routes@join_campaign() #1 SQL query",
                ),
                500,
            )

        # Controlla che l'utente non sia un membro della campagna altrimenti lo porta alla pagina della campagna
        campagne_id = [x["code"] for x in campagne]
        if not code in campagne_id:
            campaign = functions.get_campaign_from_code(MAINDB, code)
            if campaign == False:
                return (
                    jsonify(
                        description="SQL query failure.",
                        info="Error at: app/routes@join_campaign() #2 SQL query",
                    ),
                    500,
                )
            if api_functions.empty_input(campaign):
                return redirect(url_for("profile"))
            return (
                render_template(
                    "join.html",
                    campaign=campaign,
                    code=code,
                    campagne=campagne,
                    token=session["Token"],
                ),
                200,
            )
        else:
            return redirect(url_for("campaign", code=code))
    else:
        return redirect(url_for("login"))
