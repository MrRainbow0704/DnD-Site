from flask import render_template, redirect, session, url_for, flash
import json
from . import app, UsersDb
from .api import routes as api_routes
from .api.functions import SQL_query


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


@app.route("/profile")
def profilo():
    if "Id" in session:
        res = SQL_query(
            UsersDb, "SELECT * FROM Users WHERE Id=?", (session["Id"],), single=True
        )
        return render_template("profile.html", campagne=json.loads(res["Campaign"]))
    else:
        return redirect(url_for("login"))


@app.route("/campaign/<code>")
def campaign(code):
    if "Id" in session:
        res = SQL_query(
            UsersDb, "SELECT * FROM Users WHERE Id=?", (session["Id"],), single=True
        )
        return render_template("campaign.html", code=code, campagne=json.loads(res["Campaign"]))
    else:
        return redirect(url_for("login"))
