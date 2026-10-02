"""
Capa de acceso a la DB. Define tablas y funciones de inserción.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "consumo.db"


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True, parents=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ipc_regional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            fecha TEXT,
            division TEXT,
            indice REAL,
            var_mensual REAL,
            var_interanual REAL,
            scraped_at TEXT,
            UNIQUE(region, fecha, division)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cba_regional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            fecha TEXT,
            valor REAL,
            scraped_at TEXT,
            UNIQUE(region, fecha)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trends_region (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            region TEXT,
            interes INTEGER,
            fecha TEXT,
            scraped_at TEXT,
            UNIQUE(keyword, region, fecha)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS precios_producto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT,
            categoria TEXT,
            comercio TEXT,
            region TEXT,
            precio REAL,
            fecha TEXT,
            scraped_at TEXT,
            UNIQUE(producto, comercio, fecha)
        )
    """)
    conn.commit()
    return conn


def upsert_ipc(conn, row):
    conn.execute("""
        INSERT OR REPLACE INTO ipc_regional
        (region, fecha, division, indice, var_mensual, var_interanual, scraped_at)
        VALUES (?,?,?,?,?,?,?)
    """, (
        row["region"], row["fecha"], row["division"],
        row.get("indice"), row.get("var_mensual"), row.get("var_interanual"),
        datetime.now().isoformat()
    ))
    conn.commit()


def upsert_cba(conn, row):
    conn.execute("""
        INSERT OR REPLACE INTO cba_regional
        (region, fecha, valor, scraped_at)
        VALUES (?,?,?,?)
    """, (
        row["region"], row["fecha"], row["valor"],
        datetime.now().isoformat()
    ))
    conn.commit()


def upsert_trends(conn, row):
    conn.execute("""
        INSERT OR REPLACE INTO trends_region
        (keyword, region, interes, fecha, scraped_at)
        VALUES (?,?,?,?,?)
    """, (
        row["keyword"], row["region"], row["interes"],
        row["fecha"], datetime.now().isoformat()
    ))
    conn.commit()


def upsert_precio(conn, row):
    conn.execute("""
        INSERT OR REPLACE INTO precios_producto
        (producto, categoria, comercio, region, precio, fecha, scraped_at)
        VALUES (?,?,?,?,?,?,?)
    """, (
        row["producto"], row.get("categoria", ""), row.get("comercio", ""),
        row.get("region", ""), row["precio"], row["fecha"],
        datetime.now().isoformat()
    ))
    conn.commit()