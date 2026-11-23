"""Pruebas de la interfaz con el modelo entrenado real (se omiten si aún no existe)."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src import database as db
from src.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / 'models' / 'modelo.joblib').exists(), reason='modelo no entrenado')


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'app.db')
    return AppTest.from_file(str(ROOT / 'app' / 'app.py'), default_timeout=90).run()


def _zone_of(appliance):
    catalog = load_catalog()
    return catalog.loc[catalog['aparato'] == appliance, 'zona'].iloc[0]


def test_app_loads_without_errors(app):
    assert not app.exception
    assert {b.key for b in app.button} >= {'go_top', 'go_bottom'}


def test_direct_watts_flow_saves_history(app):
    app.radio[0].set_value('Ya conozco mis vatios').run()
    app.button(key='go_top').click().run()
    assert not app.exception and not app.error
    saved = db.list_measurements()
    assert len(saved) == 1
    # 130 (cocina) + 0 (lavandería) + 600 (ducha o aire) + 470 (sala): 1200 W por defecto
    assert abs(saved.iloc[0]['Global_active_power'] - 1.2) < 1e-9


def test_appliance_picker_flow(app):
    shower, tv = 'Ducha eléctrica', 'Televisor'
    app.session_state[f'pick_{_zone_of(shower)}'] = [shower]
    app.session_state[f'pick_{_zone_of(tv)}'] = [tv]
    app.run()
    app.number_input(key=f'min_{shower}').set_value(10).run()
    # 4500 W x 10/30 + 100 W x 30/30 = 1600 W
    app.button(key='go_top').click().run()
    assert not app.exception and not app.error
    saved = db.list_measurements()
    assert len(saved) == 1 and abs(saved.iloc[0]['Global_active_power'] - 1.6) < 1e-9


def test_zero_consumption_is_rejected(app):
    app.radio[0].set_value('Ya conozco mis vatios').run()
    for key in ('f_cocina', 'f_lav', 'f_cal', 'f_otros'):
        app.number_input(key=key).set_value(0.0)
    app.button(key='go_top').click().run()
    assert app.error and db.list_measurements().empty
