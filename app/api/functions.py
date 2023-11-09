from flask import session
from pathlib import Path
from os import remove
from typing import Literal, Callable
import re as regex
import sqlite3
import hashlib


class SqliteDatabase:
    def __init__(self, path: str) -> None:
        self.__path = Path(path).resolve()
        dir = self.__path.parent
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
            with open(self.__path, "x") as f:
                ...

        self.__conn = sqlite3.connect(path)

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def conn(self) -> sqlite3.Connection:
        return self.__conn

    def query(self, sqlString: str, sqlParam: tuple | dict = None) -> list:
        if sqlParam is None:
            sqlParam = ()

        # Inizializza il cursore
        cur = self.conn.cursor()

        # Esegui la query aggiornando il database se necessario
        cur.execute(sqlString, sqlParam)
        if (
            sqlString.count("UPDATE")
            or sqlString.count("DELETE")
            or sqlString.count("INSERT")
        ):
            self.conn.commit()

        # Get all the resoults of the query
        res = cur.fetchall()

        # Chiudi il cursore
        cur.close()
        return res

    def delete(self):
        self.__conn.close()
        remove(self.path)


def start_database(
    dbPath: str, sqlString: str, sqlParam: tuple | dict = None
) -> SqliteDatabase:
    UsersDb = SqliteDatabase(dbPath)
    UsersDb.query(sqlString, sqlParam)
    return UsersDb


def empty_input(*args: str) -> bool:
    for i in args:
        if not i:
            return True
    return False


def invalid_name(name: str) -> bool:
    if not regex.match(r"^[a-zA-Z_]{4,32}$", name):
        return True
    return False


def get_name(conn: SqliteDatabase, name: str) -> Literal[False] | list:
    row = conn.query("SELECT * FROM Users WHERE UserName = ?", (name,))
    if row:
        return row
    return False


def create_user(conn: SqliteDatabase, name: str, pwd: str) -> None:
    hashedPwd = hash_password(pwd)
    conn.query("INSERT INTO Users (UserName, Pwd) VALUES (?, ?)", (name, hashedPwd))


def login_user(conn: SqliteDatabase, name: str, pwd: str) -> bool:
    getNameResult = get_name(conn, name)

    if not getNameResult:
        return False

    pwdHashed = getNameResult[2]

    if not verify_password(pwd, pwdHashed):
        return False
    session["Id"] = getNameResult[0]
    session["UserName"] = getNameResult[1]
    session["LoggedIn"] = True
    return True


def search_user(conn: SqliteDatabase, name: str) -> dict[str, str | list | None]:
    result = conn.query("SELECT * FROM Users WHERE UserName LIKE ?", (f"%{name}%",))

    if len(result) > 0:
        return {"name": name, "result": result[0]}
    else:
        return {"name": name, "result": None}


def get_users(conn: SqliteDatabase, campaign: str) -> dict[str, list] | None:
    result = conn.query("SELECT * FROM Users WHERE Campaign=?", (campaign,))
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
        if session["loggedIn"]:
            return func(*args, **kwargs)
        else:
            return {"code": 401, "status": "Unauthorized"}

    return wrapper
