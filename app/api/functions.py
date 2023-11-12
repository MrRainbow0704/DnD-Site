from flask import session, redirect, url_for
from pathlib import Path
from os import remove
from typing import Literal, Callable, Any
import re as regex
import sqlite3
import hashlib


def SQL_query(
    db: str | Path, sqlString: str, sqlParam: tuple | dict = None, single=False
) -> dict[str, str] | list[dict[str, str]]:
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
    if single:
        res = cur.fetchone()
        if res is None:
            res = {}
        else:
            res = dict(res)
    else:
        res = cur.fetchall()
        error = False
        for row in res:
            if row is None:
                error = True
                res = []
                break
        if not error:
            res = list(map(dict, res))
    # Chiudi il cursore
    cur.close()
    conn.close()
    return res


def start_database(
    dbPath: str | Path,
    sqlString: str,
    sqlParam: tuple | dict = None,
) -> None:
    if sqlParam is None:
        sqlParam = ()
    dir = Path(dbPath).resolve().parent
    if not dir.exists():
        dir.mkdir(parents=True, exist_ok=True)
        with open(dbPath, "x") as f:
            ...
    else:
        SQL_query(dbPath, sqlString, sqlParam)
    return None


def empty_input(*args: Any) -> bool:
    for i in args:
        if i is None or i == "":
            return True
    return False


def invalid_name(name: str) -> bool:
    if not regex.match(r"^[a-zA-Z0-9_]{4,32}$", name):
        return True
    return False


def get_name(db: str | Path, name: str) -> Literal[False] | dict:
    row = SQL_query(db, "SELECT * FROM Users WHERE UserName = ?", (name,), single=True)
    print("get_name(): {row=}")
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

    pwdHashed = getNameResult["Pwd"]
    print(f"login_user(): {pwdHashed=}\n{getNameResult}")
    if not verify_password(pwd, pwdHashed):
        return False
    session["Id"] = getNameResult["Id"]
    session["UserName"] = getNameResult["UserName"]
    return True


def search_user(db: str | Path, name: str) -> dict[str, dict[str, str] | None]:
    result = SQL_query(db, "SELECT * FROM Users WHERE UserName LIKE ?", (f"%{name}%",))

    if len(result) > 0:
        return {"name": name, "result": result}
    else:
        return {"name": name, "result": None}


def get_players(db: str | Path, campaign: str) -> dict[str, dict[str, str]] | None:
    result = SQL_query(db, "SELECT * FROM Users WHERE Campaign=?", (campaign,))
    if result:
        return {"result": result}
    else:
        return None


def hash_password(password: str) -> str:
    hashedPassword = hashlib.sha256(password.encode()).hexdigest()
    return hashedPassword


def verify_password(inputPwd: str, hashedPwd: str) -> bool:
    print(
        f"verify_password(): {inputPwd=}",
        "\n",
        f"{hash_password(inputPwd)=}",
        "\n",
        f"{hashedPwd=}",
    )
    return hash_password(inputPwd) == hashedPwd
