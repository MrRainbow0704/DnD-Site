from flask import render_template, redirect, session, url_for
import json
from .api import routes as api_routes
from .api import api_functions
from . import app, MainDb, functions, DbHostName, DbUserName, DbUserPassword


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sign-in")
def sign_in():
    return render_template("sign_in.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/logout")
def logout():
    if "Id" in session:
        api_routes.logout()
        return redirect(url_for("login"))


@app.route("/profilo")
def profile():
    if "Id" in session:
        res = api_functions.get_name(MainDb, session["UserName"])
        return render_template("profile.html", campagne=json.loads(res["Campaigns"]))
    else:
        return redirect(url_for("login"))


@app.route("/campagna/<code>")
def campaign(code):
    if "Id" in session:
        res = functions.SQL_query(
            MainDb, "SELECT * FROM Users WHERE Id=?;", (session["Id"],), single=True
        )
        campagnie = json.loads(res["Campaigns"])
        if code in campagnie:
            CampaignDb = functions.db_connect(
                DbHostName, DbUserName, DbUserPassword, f"dnd_site_campaign_{code}"
            )
            res = functions.SQL_query(
                CampaignDb,
                "SELECT * FROM Players WHERE UserId=?;",
                (session["Id"],),
                single=True,
            )
            player = json.loads(res)
            return render_template(
                "campaign.html", code=code, campagne=campagnie, player=player
            )
        else:
            return redirect(url_for("profile"))
    else:
        return redirect(url_for("login"))
