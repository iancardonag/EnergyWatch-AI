"""El historial de ejemplo se genera con ventanas reales y queda ordenado en el tiempo."""

from datetime import datetime
from pathlib import Path
import pytest
from src import database as db
from src.seed_demo import seed

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / 'models' / 'modelo.joblib').exists(), reason='modelo no entrenado')


def test_seed_saves_varied_labeled_history(tmp_path):
    path = tmp_path / 'demo.db'
    assert seed(20, path=path, now=datetime(2026, 1, 15)) == 20
    history = db.list_measurements(path=path)
    assert len(history) == 20
    assert history['etiqueta'].str.startswith('Ejemplo').all()
    assert history['creado'].nunique() == 20
    assert history['nivel'].nunique() >= 2
