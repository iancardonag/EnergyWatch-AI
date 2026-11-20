import pandas as pd
import pytest
from src.catalog import describe_scenario, load_catalog, totals_from_appliances


def test_catalog_has_expected_columns_and_zones():
    catalog = load_catalog()
    assert len(catalog) >= 25
    assert {'aparato', 'potencia_tipica_w', 'zona'} <= set(catalog.columns)
    assert set(catalog['zona']) == {'cocina', 'lavanderia', 'agua_aire', 'otros'}


def test_totals_by_zone_and_duty_cycle():
    selection = pd.DataFrame(
        {
            'potencia_tipica_w': [2250, 4500, 100],
            'zona': ['cocina', 'agua_aire', 'otros'],
            'cantidad': [1, 1, 2],
            'minutos': [30, 15, 30],
        }
    )
    totals = totals_from_appliances(selection)
    assert totals['cocina'] == 2250
    assert totals['agua_aire'] == 2250  # 4500 W encendida la mitad de la ventana
    assert totals['total_w'] == 2250 + 2250 + 200


def test_invalid_minutes_rejected():
    selection = pd.DataFrame({'potencia_tipica_w': [100], 'zona': ['otros'], 'cantidad': [1], 'minutos': [45]})
    with pytest.raises(ValueError):
        totals_from_appliances(selection)


def test_scenarios():
    assert 'Consumo base' in describe_scenario(0.3)
    assert 'Pico' in describe_scenario(4.5)
