"""
ATELIER · db.py
SQLite mínimo para guardar las solicitudes de colaboración de la beta.
El archivo se crea solo en data/atelier.db la primera vez que se ejecuta la app.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "atelier.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS solicitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creada TEXT NOT NULL,
            modo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            contacto TEXT NOT NULL,
            rol TEXT,
            destino TEXT,
            mensaje TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creada TEXT NOT NULL,
            calificacion INTEGER NOT NULL,
            pagina TEXT,
            nombre TEXT,
            mensaje TEXT NOT NULL
        )""")


def add_request(modo, nombre, contacto, rol="", destino="", mensaje=""):
    with _conn() as c:
        c.execute("INSERT INTO solicitudes (creada, modo, nombre, contacto, rol, destino, mensaje) VALUES (?,?,?,?,?,?,?)",
                  (datetime.now().isoformat(timespec="minutes"), modo, nombre, contacto, rol, destino, mensaje))


def all_requests():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM solicitudes ORDER BY id DESC")]


def add_feedback(calificacion, mensaje, pagina="", nombre=""):
    with _conn() as c:
        c.execute("INSERT INTO comentarios (creada, calificacion, pagina, nombre, mensaje) VALUES (?,?,?,?,?)",
                  (datetime.now().isoformat(timespec="minutes"), calificacion, pagina, nombre, mensaje))


def all_feedback():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM comentarios ORDER BY id DESC")]


def feedback_average():
    with _conn() as c:
        row = c.execute("SELECT AVG(calificacion) a, COUNT(*) n FROM comentarios").fetchone()
        return (round(row["a"], 1) if row["a"] else 0, row["n"])
