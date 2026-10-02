"""
INDEC - IPC regional y Canasta Basica Alimentaria.
Prueba multiples URLs porque INDEC las cambia seguido.
"""
import sys, io
from pathlib import Path
import urllib3
import requests
import pandas as pd

urllib3.disable_warnings()

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn, upsert_ipc, upsert_cba

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

REGIONES = [
    "Gran Buenos Aires", "Pampeana", "Noreste",
    "Noroeste", "Cuyo", "Patagonia"
]

URLS_IPC = [
    "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xls",
    "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xlsx",
    "https://www.indec.gob.ar/ftp/cuadros/economia/ipc_aperturas.xlsx",
    "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_aperturas.xlsx",
]

URLS_CBA = [
    "https://www.indec.gob.ar/ftp/cuadros/economia/sh_cba_alimentos.xls",
    "https://www.indec.gob.ar/ftp/cuadros/economia/sh_cba_alimentos.xlsx",
    "https://www.indec.gob.ar/ftp/cuadros/economia/cba_alimentos.xlsx",
    "https://www.indec.gob.ar/ftp/cuadros/economia/serie_cba.xlsx",
]


def probar_urls(urls, nombre):
    """Prueba cada URL hasta que una funcione."""
    for url in urls:
        print(f"[indec] Probando {nombre}: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=60, verify=False)
            print(f"[indec]   HTTP {r.status_code} — {len(r.content)} bytes")
            if r.status_code == 200 and len(r.content) > 1000:
                return url, r.content
        except requests.exceptions.ConnectionError as e:
            print(f"[indec]   Error de conexion: {e}")
        except requests.exceptions.Timeout:
            print(f"[indec]   Timeout")
        except Exception as e:
            print(f"[indec]   Error: {e}")
    return None, None


def leer_excel(contenido, url):
    """Lee el Excel desde bytes."""
    try:
        if url.endswith(".xls"):
            return pd.read_excel(io.BytesIO(contenido), engine="xlrd", header=None)
        else:
            return pd.read_excel(io.BytesIO(contenido), engine="openpyxl", header=None)
    except Exception as e:
        print(f"[indec] Error leyendo Excel: {e}")
        return None


def procesar_cba(df):
    """Extrae filas de CBA del DataFrame crudo."""
    if df is None or df.empty:
        return []

    filas = []
    region_actual = None

    for _, row in df.iterrows():
        for cell in row:
            if pd.isna(cell):
                continue
            txt = str(cell)
            for r in REGIONES:
                if r.lower() in txt.lower():
                    region_actual = r
                    break

        if not region_actual:
            continue

        for cell in row:
            v = pd.to_numeric(cell, errors="coerce")
            if pd.notna(v) and v > 10000:
                filas.append({
                    "region": region_actual,
                    "fecha": "ultima",
                    "valor": float(v),
                })
                break

    return filas


def scrape_cba():
    url, contenido = probar_urls(URLS_CBA, "CBA")
    if not contenido:
        print("[indec] CBA: ninguna URL funciono")
        return 0

    df = leer_excel(contenido, url)
    filas = procesar_cba(df)

    if not filas:
        print("[indec] CBA: no se pudieron extraer filas")
        return 0

    conn = get_conn()
    for fila in filas:
        upsert_cba(conn, fila)
    conn.close()

    print(f"[indec] CBA OK — {len(filas)} filas")
    return len(filas)


def scrape_ipc():
    url, contenido = probar_urls(URLS_IPC, "IPC")
    if not contenido:
        print("[indec] IPC: ninguna URL funciono")
        return 0

    df = leer_excel(contenido, url)
    if df is None or df.empty:
        return 0

    print(f"[indec] IPC shape: {df.shape}")
    print(f"[indec] Primeras filas:")
    print(df.head(10).to_string())
    return 0


def scrape():
    scrape_ipc()
    scrape_cba()


if __name__ == "__main__":
    scrape()