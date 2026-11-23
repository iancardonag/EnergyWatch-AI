"""Catálogo de electrodomésticos de Colombia y escenarios de consumo de referencia.

Fuente: data/reference/consumo_electrodomesticos_colombia.xlsx (valores aproximados de
fabricantes y guías de Enel Colombia). Es referencia para la interfaz; el modelo se
entrena únicamente con el dataset real de UCI.
"""

from pathlib import Path
import pandas as pd

CATALOG_PATH = Path(__file__).resolve().parents[1] / 'data' / 'reference' / 'electrodomesticos_colombia.csv'
DEFAULT_PRICE_COP = 1000.0  # tarifa ilustrativa del Excel (COP por kWh)

# Hoja 'Rangos para el modelo' del Excel: (nombre, kW mín, kW máx, descripción)
SCENARIOS = [
    ('Consumo base', 0.2, 0.4, 'Solo nevera, router y equipos en espera (típico de madrugada).'),
    ('Consumo normal con actividad', 0.5, 2.0, 'Iluminación, TV, computador y electrodomésticos pequeños.'),
    ('Pico', 3.0, 8.0, 'Coinciden varios aparatos de resistencia (ducha eléctrica, plancha, horno, secadora).'),
]

ZONE_LABELS = {
    'cocina': 'Cocina',
    'lavanderia': 'Lavandería, nevera y luces',
    'agua_aire': 'Ducha, calentador y aire acondicionado',
    'otros': 'Otros aparatos',
}


def load_catalog(path=None):
    return pd.read_csv(path or CATALOG_PATH)


def totals_from_appliances(selection):
    """Calcula vatios promedio de una ventana de 30 min por zona.

    `selection` es un DataFrame con columnas: potencia_tipica_w, zona, cantidad, minutos
    (minutos encendido dentro de la ventana de 30). Devuelve dict con total y zonas en W.
    """
    if (selection['cantidad'] < 0).any() or ((selection['minutos'] < 0) | (selection['minutos'] > 30)).any():
        raise ValueError('Cantidad no puede ser negativa y los minutos deben estar entre 0 y 30.')
    watts = selection['potencia_tipica_w'] * selection['cantidad'] * selection['minutos'] / 30
    by_zone = watts.groupby(selection['zona']).sum()
    zones = {z: float(by_zone.get(z, 0.0)) for z in ZONE_LABELS}
    return {'total_w': float(watts.sum()), **zones}


def describe_scenario(total_kw):
    """Texto que ubica el consumo frente a los escenarios típicos de un hogar colombiano."""
    for name, low, high, detail in SCENARIOS:
        if low <= total_kw <= high:
            return f'**{name}** ({low}–{high} kW): {detail}'
    if total_kw < SCENARIOS[0][1]:
        return 'Por debajo del consumo base típico (0,2 kW): casi todo está apagado.'
    if total_kw > SCENARIOS[-1][2]:
        return 'Por encima de un pico típico (8 kW): revisa si realmente están encendidos tantos aparatos.'
    return 'Entre los escenarios típicos de referencia.'
