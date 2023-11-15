from flask import session
from typing import Literal, Any
import re as regex
import hashlib
import mysql.connector as mysql
from .. import functions


def empty_input(*args: Any) -> bool:
    for i in args:
        if i is None or i == "":
            return True
    return False


def invalid_name(name: str) -> bool:
    if not regex.match(r"^[a-zA-Z0-9_]{4,32}$", name):
        return True
    return False


def get_name(db: mysql.MySQLConnection, name: str) -> Literal[False] | dict:
    row = functions.SQL_query(
        db, "SELECT * FROM Users WHERE UserName = ?;", (name,), single=True
    )
    if len(row) > 0:
        return row
    return False


def create_user(db: mysql.MySQLConnection, name: str, pwd: str) -> None:
    hashedPwd = hash_password(pwd)
    functions.SQL_query(
        db, "INSERT INTO Users (UserName, Pwd) VALUES (?, ?);", (name, hashedPwd)
    )


def login_user(db: mysql.MySQLConnection, name: str, pwd: str) -> bool:
    getNameResult = get_name(db, name)

    if not getNameResult:
        return False

    pwdHashed = getNameResult["Pwd"]
    if not verify_password(pwd, pwdHashed):
        return False
    session["Id"] = getNameResult["Id"]
    session["UserName"] = getNameResult["UserName"]
    return True


def search_user(
    db: mysql.MySQLConnection, name: str
) -> dict[str, dict[str, str] | None]:
    result = functions.SQL_query(
        db, "SELECT * FROM Users WHERE UserName LIKE ?;", (f"%{name}%",)
    )

    if len(result) > 0:
        return {"name": name, "result": result}
    else:
        return {"name": name, "result": None}


def get_players(
    db: mysql.MySQLConnection, campaign: str
) -> dict[str, dict[str, str]] | None:
    result = functions.SQL_query(
        db, "SELECT * FROM Users WHERE Campaign=?;", (campaign,)
    )
    if result:
        return {"result": result}
    else:
        return None


def hash_password(password: str) -> str:
    hashedPassword = hashlib.sha256(password.encode()).hexdigest()
    return hashedPassword


def verify_password(inputPwd: str, hashedPwd: str) -> bool:
    return hash_password(inputPwd) == hashedPwd
