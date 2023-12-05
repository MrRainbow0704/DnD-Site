"""Il modulo che contiene l'API per l'applicazione"""

from flask import Blueprint


# Inizializza la bluepring
bp = Blueprint("api", __name__)

from . import routes
