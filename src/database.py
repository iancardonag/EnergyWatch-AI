"""Base de datos SQLite para guardar el historial de consultas del usuario.

Usa solo la librería estándar: el archivo se crea solo en data/energywatch.db.
"""

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
import pandas as pd
from src.preprocessing import FEATURES

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'energywatch.db'

# nivel: 'normal' | 'atencion' | 'alto' (lo calcula la app a partir del resultado del modelo)
COLUMNS = ['id', 'creado', 'etiqueta', 'nivel', 'mensaje', 'cluster', 'atipico', 'estado_potencia', *FEATURES]


def _connect(path=None):
    path = Path(path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path=None):
    with closing(_connect(path)) as conn, conn:
        conn.execute(f'''CREATE TABLE IF NOT EXISTS mediciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creado TEXT NOT NULL,
            etiqueta TEXT NOT NULL DEFAULT '',
            nivel TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            cluster INTEGER NOT NULL,
            atipico INTEGER NOT NULL,
            estado_potencia TEXT NOT NULL,
            {', '.join(f'{f} REAL NOT NULL' for f in FEATURES)})''')


def save_measurement(values, result, nivel, mensaje, etiqueta='', path=None):
    """Guarda una consulta. `values` es dict con FEATURES; `result` es la fila de analyze_records."""
    init_db(path)
    row = {
        'creado': datetime.now().isoformat(timespec='seconds'),
        'etiqueta': etiqueta.strip()[:80],
        'nivel': nivel,
        'mensaje': mensaje,
        'cluster': int(result['cluster']),
        'atipico': int(bool(result['statistical_outlier'])),
        'estado_potencia': str(result['power_status']),
        **{f: float(values[f]) for f in FEATURES},
    }
    cols = ', '.join(row)
    marks = ', '.join('?' for _ in row)
    with closing(_connect(path)) as conn, conn:
        cur = conn.execute(f'INSERT INTO mediciones ({cols}) VALUES ({marks})', list(row.values()))
        return cur.lastrowid


def list_measurements(limit=500, path=None):
    init_db(path)
    with closing(_connect(path)) as conn:
        rows = conn.execute('SELECT * FROM mediciones ORDER BY id DESC LIMIT ?', (int(limit),)).fetchall()
    frame = pd.DataFrame([dict(r) for r in rows], columns=COLUMNS)
    if len(frame):
        frame['creado'] = pd.to_datetime(frame['creado'])
    return frame


def delete_measurement(measurement_id, path=None):
    init_db(path)
    with closing(_connect(path)) as conn, conn:
        return conn.execute('DELETE FROM mediciones WHERE id = ?', (int(measurement_id),)).rowcount


def clear_all(path=None):
    init_db(path)
    with closing(_connect(path)) as conn, conn:
        return conn.execute('DELETE FROM mediciones').rowcount
