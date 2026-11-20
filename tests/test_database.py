import pandas as pd
from src import database as db
from src.advice import verdict, tips, daily_cost
from src.simple_input import from_simple, to_simple, zones_exceed_total
from src.preprocessing import FEATURES, validate_frame


def _result(outlier, status):
    return pd.Series({'cluster': -1 if outlier else 0, 'statistical_outlier': outlier, 'power_status': status})


def test_from_simple_is_valid_for_model():
    values = from_simple(1200, 130, 0, 600)
    assert list(values) == FEATURES
    validate_frame(pd.DataFrame([values]))
    assert values['Global_active_power'] == 1.2
    assert values['Sub_metering_3'] == 10
    assert abs(to_simple(values)['cocina_w'] - 130) < 1e-9


def test_zone_consistency():
    assert zones_exceed_total(500, 400, 400, 0)
    assert not zones_exceed_total(1200, 130, 0, 600)


def test_verdict_levels():
    assert verdict(_result(True, 'Potencia elevada'))[0] == 'alto'
    assert verdict(_result(False, 'Potencia elevada'))[0] == 'atencion'
    assert verdict(_result(True, 'Potencia dentro'))[0] == 'atencion'
    assert verdict(_result(False, 'Potencia dentro'))[0] == 'normal'
    assert tips(1000, 600, 0, 0, 'normal')
    assert daily_cost(1000, 500) == (24, 12000)


def test_database_roundtrip(tmp_path):
    path = tmp_path / 'test.db'
    values = from_simple(1200, 130, 0, 600)
    new_id = db.save_measurement(values, _result(False, 'Potencia dentro'), 'normal', 'ok', 'prueba', path=path)
    frame = db.list_measurements(path=path)
    assert len(frame) == 1 and frame.iloc[0]['etiqueta'] == 'prueba'
    assert frame.iloc[0]['Global_active_power'] == 1.2
    assert db.delete_measurement(new_id, path=path) == 1
    assert db.list_measurements(path=path).empty
    db.save_measurement(values, _result(True, 'x'), 'alto', 'm', path=path)
    assert db.clear_all(path=path) == 1
