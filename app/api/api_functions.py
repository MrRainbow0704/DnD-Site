from flask import session, jsonify, make_response, Response
from typing import Literal, Any
import mysql.connector as mysql
import re as regex
import hashlib
import json
from config import PEPPER
from .. import functions


def empty_input(*args: Any) -> bool:
    """Controlla che nessuno degli argomenti sia nullo o vuoto.

    Args:
        *args (Any): Argomenti da passare alla funzione
    Returns:
        bool: Se il valore è vuoto o no.
    """
    for i in args:
        if not bool(i) and type(i) != int:
            return True
    return False


def invalid_name(name: str) -> bool:
    """Controlla se il nome è valido.

    Args:
        name (str): Nome da conrollare.

    Returns:
        bool: Se il nome è valido o no.
    """
    if not regex.match(r"^[a-zA-Z0-9_]{4,32}$", name):
        return True
    return False


def get_name(db: mysql.MySQLConnection, name: str) -> Literal[False] | dict:
    """Ottiene tutte le righe di un utente in base al suo nome.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        name (str): Nome dell'utente.

    Returns:
        Literal[False] | dict: Un dizionario rappresentante la riga. Se non trova nulla False.
    """
    row = functions.SQL_query(
        db, "SELECT * FROM Users WHERE UserName = %s;", (name,), single=True
    )
    if row:
        return row[0]
    return False


def create_user(db: mysql.MySQLConnection, name: str, pwd: str, salt: str) -> None:
    """Crea un utente nel database criptandone la password.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        name (str): Nome dell'utente.
        pwd (str): Password dell'utente (in chiaro).
    """
    hashedPwd = hash_password(pwd, salt)
    functions.SQL_query(
        db,
        "INSERT INTO Users (UserName, Pwd, Salt) VALUES (%s, %s, %s);",
        (name, hashedPwd, salt),
    )


def login_user(db: mysql.MySQLConnection, name: str, pwd: str) -> bool:
    """Esegue il login di un utente.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        name (str): Nome dell'utente.
        pwd (str): Password dell'utente (in chiaro).

    Returns:
        bool: Se l'operazione è andata a buon fine o no.
    """
    getNameResult = get_name(db, name)

    if not getNameResult:
        return False

    pwdHashed = getNameResult["Pwd"]
    salt = getNameResult["Salt"]
    if not verify_password(pwd, salt, pwdHashed):
        return False
    session["Id"] = getNameResult["Id"]
    session["UserName"] = getNameResult["UserName"]
    return True


def get_players(
    db: mysql.MySQLConnection, campaign: str
) -> list[dict[str, str]] | None:
    """WIP Restituisce le righe di tutti i giocatori che partecipano a una certa campagna.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        campaign (str): Codice della campagna.

    Returns:
        list[dict[str, str]] | None: Una lista di dizionari rappresentante le righe. Se non trova nulla None.
    """
    result = functions.SQL_query(
        db, "SELECT * FROM Users WHERE Campaign=%s;", (campaign,)
    )
    if result:
        return result
    else:
        return None


def hash_password(password: str, salt: str) -> str:
    """Cripta una password.

    Args:
        password (str): Password (in chiaro).

    Returns:
        str: Password (criptata).
    """
    return hashlib.sha512(str(salt + password + PEPPER).encode()).hexdigest()


def verify_password(inputPwd: str, salt: str, hashedPwd: str) -> bool:
    """Verifica che le password corrispondano.

    Args:
        inputPwd (str): Password da controllare (in chiaro).
        hashedPwd (str): Password originale (criptata).

    Returns:
        bool: Se le password corrispondono o no.
    """
    return hash_password(inputPwd, salt) == hashedPwd


def json_response(code: int, response: Any) -> Response:
    return make_response(jsonify(response), code)
