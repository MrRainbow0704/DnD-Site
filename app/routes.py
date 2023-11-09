from flask import render_template, redirect, request, session, url_for
from .api import functions
from . import app


@app.route("/")
def index():
    return render_template("index.html")