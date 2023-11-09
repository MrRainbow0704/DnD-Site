from flask import session
from pathlib import Path
from os import remove
from typing import Literal, Callable
import re as regex
import sqlite3
import hashlib


def SQL_query(db: str | Path, sqlString: str, sqlParam: tuple | dict = None) -> dict[str, str]:
    if sqlParam is None:
        sqlParam = ()
    # Inizializza il cursore
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Esegui la query aggiornando il database se necessario
    cur.execute(sqlString, sqlParam)
    if (
        sqlString.count("UPDATE")
        or sqlString.count("DELETE")
        or sqlString.count("INSERT")
    ):
        conn.commit()
    # Get all the resoults of the query
    res = cur.fetchall()
    # Chiudi il cursore
    cur.close()
    conn.close()
    return res


def start_database(
    dbPath: str | Path, sqlString: str, sqlParam: tuple | dict = None
) -> None:
    dir = Path(dbPath).resolve().parent
    if not dir.exists():
        dir.mkdir(parents=True, exist_ok=True)
        with open(dbPath, "x") as f:
            ...
    SQL_query(dbPath, sqlString, sqlParam)
    return None


def empty_input(*args: str) -> bool:
    for i in args:
        if not i:
            return True
    return False


def invalid_name(name: str) -> bool:
    if not regex.match(r"^[a-zA-Z_]{4,32}$", name):
        return True
    return False


def get_name(db: str | Path, name: str) -> Literal[False] | list:
    row = SQL_query(db, "SELECT * FROM Users WHERE UserName = ?", (name,))
    if len(row) > 0:
        return row
    return False


def create_user(db: str | Path, name: str, pwd: str) -> None:
    hashedPwd = hash_password(pwd)
    SQL_query(db, "INSERT INTO Users (UserName, Pwd) VALUES (?, ?)", (name, hashedPwd))


def login_user(db: str | Path, name: str, pwd: str) -> bool:
    getNameResult = get_name(db, name)

    if not getNameResult:
        return False

    pwdHashed = getNameResult[2]

    if not verify_password(pwd, pwdHashed):
        return False
    session["Id"] = getNameResult[0]
    session["UserName"] = getNameResult[1]
    session["LoggedIn"] = True
    return True


def search_user(db: str | Path, name: str) -> dict[str, str | list | None]:
    result = SQL_query(db, "SELECT * FROM Users WHERE UserName LIKE ?", (f"%{name}%",))

    if len(result) > 0:
        return {"name": name, "result": result}
    else:
        return {"name": name, "result": None}


def get_players(db: str | Path, campaign: str) -> dict[str, list] | None:
    result = SQL_query(db, "SELECT * FROM Users WHERE Campaign=?", (campaign,))
    if result:
        return {"result": result}
    else:
        return None


def hash_password(password: str) -> str:
    hashedPassword = hashlib.sha256(password.encode()).hexdigest()
    return hashedPassword


def verify_password(inputPwd: str, hashedPwd: str) -> bool:
    return hashlib.sha256(inputPwd.encode()).hexdigest() == hashedPwd


def login_required(func: Callable, *args, **kwargs):
    def wrapper():
        if "LoggedIn" in session and session["LoggedIn"]:
            return func(*args, **kwargs)
        else:
            return {"code": 401, "status": "Unauthorized"}
    return wrapper
