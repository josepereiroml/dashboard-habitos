"""
Orquestador de scrapers.
"""
import subprocess
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

ROOT = Path(__file__).resolve().parent
SCRAPERS_DIR = ROOT / "scrapers"

JOBS = [
    "indec.py",
    "trends_region.py",
]


def python_exe():
    """Devuelve el Python del venv si existe, si no el actual."""
    venv_py = ROOT / "venv" / "Scripts" / "python.exe"
    return str(venv_py) if venv_py.exists() else sys.executable


def run_all():
    py = python_exe()
    print(f"Python: {py}")
    print(f"Proyecto: {ROOT}")
    print(f"Scrapers: {SCRAPERS_DIR}\n")

    for job in JOBS:
        script = SCRAPERS_DIR / job
        if not script.exists():
            print(f"[skip] No existe: {script.name}")
            continue

        print(f"=== {script.name} ===")
        try:
            result = subprocess.run(
                [py, script.name],
                cwd=str(SCRAPERS_DIR),
                timeout=900,
            )
            if result.returncode != 0:
                print(f"[warn] {script.name} termino con codigo {result.returncode}")
        except subprocess.TimeoutExpired:
            print(f"[timeout] {script.name} tardo mas de 15 min")
        print()


if __name__ == "__main__":
    run_all()

    if not HAS_SCHEDULE:
        print("[info] 'schedule' no instalado. Corrida unica.")
        sys.exit(0)

    schedule.every(12).hours.do(run_all)
    print("[info] Proxima corrida en 12 h. Ctrl+C para salir.\n")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[info] Detenido por el usuario.")