from flask import render_template, redirect, session, url_for, flash
from . import app


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sign-in")
def sign_in():
    return render_template("sign_in.html")


@app.route("/profilo")
def profilo():
    if "LoggedIn" in session and session["LoggedIn"]:
        return render_template("profilo.html")
    else:
        return redirect(url_for('sign_in'))
