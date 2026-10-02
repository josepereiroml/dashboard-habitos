"""
Precios Claros / SEPA - precios de supermercados por región.
Requiere la URL actual del dataset de la Secretaría de Comercio.
"""
import sys, io
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn, upsert_precio

# Placeholder - hay que actualizar con la URL vigente
URL_DATASET = "https://datos.produccion.gob.ar/dataset/sepa-precios"


def scrape():
    print("[sepa] Endpoint no configurado. Ver comentarios en el script.")
    print("[sepa] Alternativa: descargar el CSV desde datos.produccion.gob.ar")
    # TODO: cuando tengas la URL directa al CSV, descomentás esto:
    #
    # r = requests.get(URL_CSV, timeout=120)
    # df = pd.read_csv(io.StringIO(r.text))
    # conn = get_conn()
    # for _, row in df.iterrows():
    #     upsert_precio(conn, {
    #         "producto": row["productos_descripcion"],
    #         "categoria": row.get("categoria", ""),
    #         "comercio": row["sucursales_nombre"],
    #         "region": row.get("provincia", ""),
    #         "precio": float(row["productos_precio_lista"]),
    #         "fecha": datetime.now().strftime("%Y-%m-%d"),
    #     })
    # conn.close()


if __name__ == "__main__":
    scrape()