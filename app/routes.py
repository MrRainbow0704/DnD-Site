from flask import render_template, redirect, session, url_for, flash
from . import app
from .api import routes as api_routes


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
        return render_template("profile.html")
    else:
        return redirect(url_for("login"))
