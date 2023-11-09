from flask import render_template
from .api import functions
from . import app


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profilo")
def home():
    return render_template("home.html")