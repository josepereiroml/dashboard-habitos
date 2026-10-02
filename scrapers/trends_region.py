"""
Google Trends - interes por provincia en Argentina.
Usa pytrends con pausas para evitar 429.
"""
import sys, time, random
from pathlib import Path
from datetime import datetime
from pytrends.request import TrendReq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_conn, upsert_trends

KEYWORDS = [
    "inflación",
    "aumento",
    "supermercado",
    "delivery",
    "canasta básica",
    "precios",
    "Mercado Libre",
    "PedidosYa",
    "Rappi",
    "Carrefour",
    "Coto",
    "Día",
]


def scrape():
    conn = get_conn()
    pytrends = TrendReq(hl="es-AR", tz=-180)

    time.sleep(random.uniform(10, 20))

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ok, fail = 0, 0

    for keyword in KEYWORDS:
        try:
            print(f"[trends] Consultando: {keyword}")
            pytrends.build_payload(
                [keyword],
                cat=0,
                timeframe="now 7-d",
                geo="AR",
            )
            df = pytrends.interest_by_region(
                resolution="REGION",
                inc_low_vol=True,
                inc_geo_code=True,
            )

            if df is None or df.empty:
                print(f"[trends] {keyword}: sin datos regionales")
                continue

            filas = 0
            for _, row in df.iterrows():
                region = row.get("geoName") or row.name
                interes = int(row[keyword]) if keyword in row else 0
                if interes <= 0:
                    continue
                upsert_trends(conn, {
                    "keyword": keyword,
                    "region": str(region),
                    "interes": interes,
                    "fecha": fecha_hoy,
                })
                filas += 1

            print(f"[trends] {keyword}: {filas} regiones")
            ok += 1

            time.sleep(random.uniform(15, 30))

        except Exception as e:
            fail += 1
            print(f"[trends] {keyword}: error {e}")
            time.sleep(random.uniform(30, 60))

    conn.close()
    print(f"[trends] fin: {ok} OK / {fail} fallidos")


if __name__ == "__main__":
    scrape()