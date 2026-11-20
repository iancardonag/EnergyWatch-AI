"""Convierte el resultado técnico del modelo en un mensaje simple para el usuario."""

NIVELES = {
    'normal': ('🟢', 'Todo en orden'),
    'atencion': ('🟡', 'Vale la pena revisar'),
    'alto': ('🔴', 'Consumo alto y poco habitual'),
}


def verdict(result):
    """Devuelve (nivel, mensaje) a partir de una fila de analyze_records."""
    outlier = bool(result['statistical_outlier'])
    status = str(result['power_status'])
    high = 'elevada' in status
    low = 'baja' in status
    if outlier and high:
        return 'alto', 'Tu consumo es más alto de lo normal y además la combinación de aparatos es poco habitual.'
    if high:
        return (
            'atencion',
            'Tu consumo es alto, aunque es un patrón que se repite en hogares como el de los datos de referencia.',
        )
    if outlier:
        return 'atencion', 'La combinación de consumos es poco habitual comparada con los datos de referencia.'
    if low:
        return 'normal', 'Tu consumo es bajo y es un patrón habitual.'
    return 'normal', 'Tu consumo se parece a un patrón habitual.'


def tips(total_w, cocina_w, lavanderia_w, calentador_w, nivel):
    """Consejos sencillos según la zona que más consume."""
    out = []
    zones = {
        'la cocina': cocina_w,
        'la lavandería': lavanderia_w,
        'el calentador de agua / aire acondicionado': calentador_w,
    }
    name, watts = max(zones.items(), key=lambda kv: kv[1])
    if watts > 0 and total_w > 0 and watts / total_w >= 0.4:
        out.append(
            f'{name.capitalize()} concentra {watts / total_w:.0%} de tu consumo: ahí está tu mayor oportunidad de ahorro.'
        )
    other = total_w - cocina_w - lavanderia_w - calentador_w
    if total_w > 0 and other / total_w >= 0.5:
        out.append(
            'Más de la mitad del consumo viene de otros aparatos (luces, nevera, TV, cargadores). Revisa lo que queda encendido.'
        )
    if nivel in ('alto', 'atencion'):
        out.append('Prueba desconectar aparatos que no uses y vuelve a consultar para comparar en el historial.')
    if not out:
        out.append('No hay nada especial que corregir. Sigue guardando consultas para ver cómo cambia tu consumo.')
    return out


def daily_cost(total_w, price_per_kwh):
    """kWh y costo estimado si ese consumo promedio se mantuviera 24 horas."""
    kwh = total_w / 1000 * 24
    return kwh, kwh * price_per_kwh
