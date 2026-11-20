"""Traduce datos cotidianos (vatios por zona de la casa) a las 7 variables del modelo."""

from src.preprocessing import FEATURES

# El modelo se entrenó con voltaje ~240 V. Para que el usuario no quede "lejos" de los datos solo por
# vivir en una red de 120 V, la app trabaja en vatios y usa el voltaje equivalente del entrenamiento.
MODEL_VOLTAGE = 240.0
DEFAULT_REACTIVE_KW = 0.1


def from_simple(
    total_w, cocina_w=0.0, lavanderia_w=0.0, calentador_w=0.0, voltage=MODEL_VOLTAGE, reactive_kw=DEFAULT_REACTIVE_KW
):
    """Convierte vatios promedio de la casa a las variables del dataset UCI.

    - Potencia activa: W -> kW.
    - Submedidores del dataset: Wh por minuto = W / 60 (cocina, lavandería, calentador/aire).
    - Corriente: aproximación I = P / V con el voltaje del entrenamiento.
    """
    if total_w < 0 or min(cocina_w, lavanderia_w, calentador_w) < 0:
        raise ValueError('Los consumos no pueden ser negativos.')
    if voltage <= 0:
        raise ValueError('El voltaje debe ser mayor que cero.')
    values = {
        'Global_active_power': total_w / 1000,
        'Global_reactive_power': reactive_kw,
        'Voltage': voltage,
        'Global_intensity': total_w / voltage,
        'Sub_metering_1': cocina_w / 60,
        'Sub_metering_2': lavanderia_w / 60,
        'Sub_metering_3': calentador_w / 60,
    }
    return {f: values[f] for f in FEATURES}


def zones_exceed_total(total_w, cocina_w, lavanderia_w, calentador_w):
    """True si las zonas suman claramente más que el total de la casa (dato inconsistente)."""
    return (cocina_w + lavanderia_w + calentador_w) > total_w * 1.05 + 1


def to_simple(values):
    """Inversa aproximada, para mostrar un ejemplo del dataset en vatios."""
    return {
        'total_w': values['Global_active_power'] * 1000,
        'cocina_w': values['Sub_metering_1'] * 60,
        'lavanderia_w': values['Sub_metering_2'] * 60,
        'calentador_w': values['Sub_metering_3'] * 60,
    }
