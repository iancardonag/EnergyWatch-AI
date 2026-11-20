"""Pruebas de la interfaz con el modelo entrenado real (se omiten si aún no existe)."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src import database as db

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / 'models' / 'modelo.joblib').exists(), reason='modelo no entrenado')


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'app.db')
    return AppTest.from_file(str(ROOT / 'app' / 'app.py'), default_timeout=90).run()


def test_app_loads_without_errors(app):
    assert not app.exception
    assert len(app.tabs) == 5


def test_direct_watts_flow_saves_history(app):
    app.radio[0].set_value('⚡ Ya conozco mis vatios').run()
    [b for b in app.button if b.label == 'Revisar mi consumo'][0].click().run()
    assert not app.exception and not app.error
    assert len(db.list_measurements()) == 1


def test_appliance_picker_flow(app):
    app.checkbox(key='use_Ducha eléctrica').check().run()
    app.number_input(key='min_Ducha eléctrica').set_value(10).run()
    app.checkbox(key='use_Televisor').check().run()
    # 4500 W x 10/30 + 100 W x 30/30 = 1600 W
    estimated = [m for m in app.metric if m.label == 'Consumo promedio estimado'][0]
    assert estimated.value == '1,600 W'
    [b for b in app.button if b.label == 'Revisar mi consumo'][0].click().run()
    assert not app.exception and not app.error
    saved = db.list_measurements()
    assert len(saved) == 1 and abs(saved.iloc[0]['Global_active_power'] - 1.6) < 1e-9


def test_zero_consumption_is_rejected(app):
    app.radio[0].set_value('⚡ Ya conozco mis vatios').run()
    # Los valores de un formulario solo viajan al pulsar enviar: set_value y click en la misma ejecución.
    app.number_input(key='f_total').set_value(0.0)
    [b for b in app.button if b.label == 'Revisar mi consumo'][0].click().run()
    assert app.error and db.list_measurements().empty
