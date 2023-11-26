from flask import render_template, redirect, session, url_for, abort
import json
import config
from uuid import uuid4
from .api import routes as api_routes
from .api import api_functions
from . import app, functions, MAINDB


@app.route("/")
def index():
    session["Token"] = uuid4().hex
    return render_template("index.html", token=session["Token"])


@app.route("/sign-in")
def sign_in():
    session["Token"] = uuid4().hex
    return render_template("sign_in.html", token=session["Token"])


@app.route("/login")
def login():
    session["Token"] = uuid4().hex
    return render_template("login.html", token=session["Token"])


@app.route("/logout")
def logout():
    if "Id" in session:
        api_routes.logout()
        return redirect(url_for("login"))


@app.route("/profilo")
def profile():
    if "Id" in session:
        session["Token"] = uuid4().hex
        res = api_functions.get_name(MAINDB, session["UserName"])
        return render_template(
            "profile.html",
            campagne=json.loads(res["Campaigns"]),
            token=session["Token"],
        )
    else:
        return redirect(url_for("login"))


@app.route("/campagna/<code>")
def campaign(code):
    if "Id" in session:
        session["Token"] = uuid4().hex
        res = functions.SQL_query(
            MAINDB, "SELECT * FROM Users WHERE Id=%s;", (session["Id"],), single=True
        )
        if not res:
            abort(500, description="SQL query faliure.")

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
            if not CampaignDb:
                abort(500, description="Database connection faliure (CampaignDb).")

            campagna = functions.SQL_query(
                MAINDB, "SELECT * FROM Campaigns WHERE Code=%s;", (code,), single=True
            )
            if not campagna:
                abort(500, description="SQL query faliure.")

            if campagna["DungeonMaster"] == session["Id"]:
                player = "DUNGEONMASTER"
            else:
                player = functions.SQL_query(
                    CampaignDb,
                    "SELECT * FROM Players WHERE UserId=%s;",
                    (session["Id"],),
                    single=True,
                )
                if not player:
                    abort(500, description="SQL query faliure.")
            return render_template(
                "campaign.html",
                code=code,
                campagne=campagnie,
                player=player,
                token=session["Token"],
            )
        else:
            return redirect(url_for("profile"))
    else:
        return redirect(url_for("login"))
