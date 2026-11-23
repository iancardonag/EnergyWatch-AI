"""Carga un historial de ejemplo con ventanas reales del conjunto de evaluación.

Cada consulta sale de una ventana de 30 minutos del dataset UCI (data/processed/replay_test.csv),
se analiza con el modelo entrenado y se guarda con la etiqueta "Ejemplo · ...". No son usuarios
reales: sirve para ver la app con datos desde el primer momento (demo y capturas).

Uso:  python -m src.seed_demo [cantidad]
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import joblib
import pandas as pd
from src import database as db
from src.advice import verdict
from src.predict import analyze_records
from src.preprocessing import FEATURES

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / 'data' / 'processed' / 'replay_test.csv'
MODEL = ROOT / 'models' / 'modelo.joblib'
SEED = 42


def _moment(hour):
    if hour < 6:
        return 'madrugada'
    if hour < 12:
        return 'mañana'
    if hour < 19:
        return 'tarde'
    return 'noche'


def pick_windows(replay, n=40):
    """Mezcla ventanas habituales, de consumo alto y atípicas para que el historial sea variado."""
    unusual = replay[replay['cluster'] == -1]
    high = replay[replay['statistical_outlier'].eq(False) & (replay['alert'] == 'Patrón conocido con potencia elevada')]
    rest = replay.drop(unusual.index).drop(high.index)
    parts = [
        unusual.sample(min(len(unusual), max(1, n // 8)), random_state=SEED),
        high.sample(min(len(high), max(1, n // 4)), random_state=SEED),
    ]
    taken = sum(len(p) for p in parts)
    parts.append(rest.sample(n - taken, random_state=SEED))
    return pd.concat(parts).sort_values('timestamp').reset_index(drop=True)


def seed(n=40, path=None, now=None, days=14):
    """Guarda `n` consultas de ejemplo repartidas en los últimos `days` días. Devuelve cuántas guardó."""
    bundle = joblib.load(MODEL)
    windows = pick_windows(pd.read_csv(REPLAY, parse_dates=['timestamp']), n)
    results = analyze_records(windows[FEATURES], bundle)
    now = now or datetime.now()
    step = timedelta(days=days) / max(n, 1)
    for i, (_, win) in enumerate(windows.iterrows()):
        result = results.iloc[i]
        nivel, mensaje = verdict(result)
        stamp = now - timedelta(days=days) + step * i
        label = f'Ejemplo · {_moment(win["timestamp"].hour)}'
        db.save_measurement(win[FEATURES].to_dict(), result, nivel, mensaje, label, path=path, creado=stamp)
    return len(windows)


if __name__ == '__main__':
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    print(f'{seed(count)} consultas de ejemplo guardadas en {db.DB_PATH}')
