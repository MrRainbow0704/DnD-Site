from flask import render_template, redirect, session, url_for, jsonify
import json
import config
from uuid import uuid4
from .api import routes as api_routes
from .api import api_functions
from . import app, functions, MAINDB


@app.route("/")
def index():
    """Route per la pagina index"""

    # Aggiorna il token e renderizza la pagina
    session["Token"] = uuid4().hex
    return render_template("index.html", token=session["Token"]), 200


@app.route("/sign-in")
def sign_in():
    """Route per la pagina di registrazione"""

    # Aggiorna il token e renderizza la pagina
    session["Token"] = uuid4().hex
    return render_template("sign_in.html", token=session["Token"]), 200


@app.route("/login")
def login():
    """Route per la pagina di login"""

    # Aggiorna il token e renderizza la pagina
    session["Token"] = uuid4().hex
    return render_template("login.html", token=session["Token"]), 200


@app.route("/logout")
def logout():
    """Route per la pagina di logout"""

    # Aggiorna il token e renderizza la pagina
    if "Id" in session:
        api_routes.logout()
        return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))


@app.route("/profilo")
def profile():
    """Route per la pagina profilo"""

    # Controlla che l'utente sia loggato altrimenti lo porta a login
    if "Id" in session:
        # Aggiorna il token, prende le campagne a cui l'utente partecipa e renderizza la pagina
        session["Token"] = uuid4().hex
        res = api_functions.get_name(MAINDB, session["UserName"])
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


@app.route("/campagna/<string:code>")
def campaign(code: str):
    """Route per la pagina campagna

    Args:
        code (str): Codice della campagna
    """

    # Controlla che l'utente sia loggato altrimenti lo porta a login
    if "Id" in session:
        # Aggiorna il token, prende le campagne a cui l'utente partecipa
        session["Token"] = uuid4().hex
        res = functions.SQL_query(
            MAINDB, "SELECT * FROM Users WHERE Id=%s;", (session["Id"],), single=True
        )
        if res == False:
            return (
                jsonify(
                    description="SQL query faliure.",
                    info="Error at: app/routes@campaign() #1 SQL query",
                ),
                500,
            )

        # Controlla che l'utente sia un membro della campagna altrimenti lo porta a profilo
        campagnie = json.loads(res["Campaigns"])
        campagnie_id = [x["code"] for x in campagnie]
        if code in campagnie_id:
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
                        info="Error at: app/routes@campaign() #1 database connection",
                    ),
                    500,
                )

            campagna = functions.SQL_query(
                MAINDB, "SELECT * FROM Campaigns WHERE Code=%s;", (code,), single=True
            )
            if campagna == False:
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/routes@campaign() #2 SQL query",
                    ),
                    500,
                )

            # Controlla se l'utente è il Dungeon Master, altrimenti provvede al prelievo dei dati
            if campagna["DungeonMaster"] == session["Id"]:
                player = "DUNGEONMASTER"
            else:
                player = functions.SQL_query(
                    CampaignDb,
                    "SELECT * FROM Players WHERE UserId=%s;",
                    (session["Id"],),
                    single=True,
                )
                if player == False:
                    return (
                        jsonify(
                            description="SQL query faliure.",
                            info="Error at: app/routes@campaign() #3 SQL query",
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
                        description="SQL query faliure.",
                        info="Error at: app/routes@join_campaign() #3 SQL query",
                    ),
                    500,
                )

            players = []
            for pId in json.loads(campaign["Players"]):
                pl = functions.SQL_query(
                    MAINDB, "SELECT * FROM Users WHERE Id=%s ;", (pId,), single=True
                )
                if pl == False:
                    return (
                        jsonify(
                            description="SQL query faliure.",
                            info="Error at: app/routes@join_campaign() #2 SQL query.",
                        ),
                        500,
                    )
                players.append(pl["UserName"])
            # Alla fine renderizza la pagina con tutte le sue variabili
            return (
                render_template(
                    "campaign.html",
                    campaign=campaign,
                    campagne=campagnie,
                    player=player,
                    players=players,
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
    if "Id" in session:
        # Aggiorna il token, prende le campagne a cui l'utente partecipa
        session["Token"] = uuid4().hex
        res = functions.SQL_query(
            MAINDB, "SELECT * FROM Users WHERE Id=%s;", (session["Id"],), single=True
        )
        if res == False:
            return (
                jsonify(
                    description="SQL query faliure.",
                    info="Error at: app/routes@join_campaign() #1 SQL query",
                ),
                500,
            )

        # Controlla che l'utente non sia un membro della campagna altrimenti lo porta alla pagina della campagna
        campagnie = json.loads(res["Campaigns"])
        campagnie_id = [x["code"] for x in campagnie]
        if not code in campagnie_id:
            campaign = functions.SQL_query(
                MAINDB,
                "SELECT * FROM Campaigns WHERE Code=%s;",
                (code,),
                single=True,
            )
            if campaign == False:
                return (
                    jsonify(
                        description="SQL query faliure.",
                        info="Error at: app/routes@join_campaign() #2 SQL query",
                    ),
                    500,
                )
            return (
                render_template(
                    "join.html",
                    campaign=campaign,
                    code=code,
                    campagne=campagnie,
                    token=session["Token"],
                ),
                200,
            )
        else:
            return redirect(url_for("campaign", code=code))
    else:
        return redirect(url_for("login"))
