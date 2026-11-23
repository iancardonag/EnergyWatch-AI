"""EnergyWatch AI: una casa en corte que muestra si el consumo del hogar es normal (DBSCAN + SQLite)."""

from pathlib import Path
import json
import sys
import time
import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.predict import analyze_records
from src.simple_input import from_simple, to_simple
from src.advice import NIVELES, verdict, tips, daily_cost
from src.catalog import DEFAULT_PRICE_COP, SCENARIOS, ZONE_LABELS, describe_scenario, load_catalog
from src.house import FULL_LIGHT_W, ROOMS, meter_svg, roof_svg, room_svg
from src import database as db
from src import ui
from src.seed_demo import seed

st.set_page_config(page_title='EnergyWatch AI', page_icon=str(ROOT / 'app' / 'static' / 'icon.png'), layout='wide')
st.markdown(ui.CSS, unsafe_allow_html=True)

REPLAY = ROOT / 'data' / 'processed' / 'replay_test.csv'
WINDOW_MINUTES = 30  # el modelo analiza ventanas de 30 minutos
MODE_APPLIANCES = 'Elegir mis electrodomésticos'
MODE_WATTS = 'Ya conozco mis vatios'
WATT_KEYS = {'cocina': 'f_cocina', 'lavanderia': 'f_lav', 'agua_aire': 'f_cal', 'otros': 'f_otros'}
WATT_DEFAULTS = {'f_cocina': 130.0, 'f_lav': 0.0, 'f_cal': 600.0, 'f_otros': 470.0}
WATT_MAX = {'cocina': 6000.0, 'lavanderia': 6000.0, 'agua_aire': 11000.0, 'otros': 8000.0}


@st.cache_resource
def load_model():
    return joblib.load(ROOT / 'models' / 'modelo.joblib')


@st.cache_data
def load_meta():
    return json.loads((ROOT / 'models' / 'metadata.json').read_text(encoding='utf-8'))


@st.cache_data
def load_replay():
    return pd.read_csv(REPLAY, parse_dates=['timestamp'])


@st.cache_data
def load_appliances():
    return load_catalog()


def show_figure(fig):
    st.pyplot(fig, clear_figure=True, width='stretch')
    ui.close(fig)


def check_consumption(zones, price, etiqueta):
    """Evalúa el consumo con el modelo, muestra el resultado y lo guarda. Devuelve el nivel o None."""
    total_w = sum(zones.values())
    if total_w <= 0:
        st.error('El consumo total debe ser mayor que 0 W. Marca al menos un aparato o escribe un valor.')
        return None
    cocina_w, lavanderia_w, agua_aire_w = zones['cocina'], zones['lavanderia'], zones['agua_aire']
    try:
        values = from_simple(total_w, cocina_w, lavanderia_w, agua_aire_w)
        result = analyze_records(pd.DataFrame([values]), bundle).iloc[0]
        nivel, mensaje = verdict(result)
        label, _ = NIVELES[nivel]
        kwh, cost = daily_cost(total_w, price)
        limits = bundle['thresholds']
        st.markdown(
            ui.result_card(
                nivel, label, mensaje, total_w, limits['power_p05'], limits['power_p95'],
                kwh, cost if price > 0 else 0, int(result['cluster']),
            ),
            unsafe_allow_html=True,
        )
        st.caption(describe_scenario(total_w / 1000).replace('**', ''))
        st.markdown('**Qué puedes hacer**')
        for tip in tips(total_w, cocina_w, lavanderia_w, agua_aire_w, nivel):
            st.markdown(f'- {tip}')
        if REPLAY.exists():
            with st.expander('Ver dónde cae tu consulta entre datos reales'):
                show_figure(ui.density_map(load_replay(), (values['Global_active_power'], values['Sub_metering_3'])))
        db.save_measurement(values, result, nivel, mensaje, etiqueta)
        st.caption('Consulta guardada en tu historial. Es orientativa: no confirma fallas ni riesgos eléctricos.')
        return nivel
    except Exception as exc:
        st.error(f'No fue posible revisar el consumo: {exc}')
        return None


def room_card(zone, mode, catalog):
    """Tarjeta de una habitación. Devuelve los vatios promedio de su zona."""
    watts = 0.0
    with st.container(key=f'room_{zone}'):
        head = st.empty()
        if mode == MODE_APPLIANCES:
            items = catalog[catalog['zona'] == zone]
            chosen = st.pills(
                ZONE_LABELS[zone], list(items['aparato']), selection_mode='multi', key=f'pick_{zone}',
                label_visibility='collapsed',
            )
            for name in chosen or []:
                power = float(items.loc[items['aparato'] == name, 'potencia_tipica_w'].iloc[0])
                col_name, col_qty, col_min = st.columns([3, 1, 1])
                col_name.markdown(f'<div class="ew-appname"><b>{name}</b><br>{power:.0f} W</div>', unsafe_allow_html=True)
                qty = col_qty.number_input('Cant.', 1, 10, 1, key=f'qty_{name}')
                mins = col_min.number_input(
                    'Min', 1, WINDOW_MINUTES, WINDOW_MINUTES, key=f'min_{name}',
                    help=f'Minutos encendido de los últimos {WINDOW_MINUTES}',
                )
                watts += power * qty * mins / WINDOW_MINUTES
        else:
            watts = st.number_input(
                f'{ZONE_LABELS[zone]} (W)', 0.0, WATT_MAX[zone], step=10.0, key=WATT_KEYS[zone],
                label_visibility='collapsed',
            )
        head.markdown(ui.room_head(ROOMS[zone][2], watts, room_svg(zone, watts)), unsafe_allow_html=True)
    return float(watts)


if not (ROOT / 'models' / 'modelo.joblib').exists():
    st.markdown(ui.header(), unsafe_allow_html=True)
    st.warning('Aún falta entrenar el modelo. Ejecuta estos comandos en la carpeta del proyecto:')
    st.code('pip install -r requirements.txt\npython -m src.train\nstreamlit run app/app.py')
    st.stop()

try:
    bundle, meta = load_model(), load_meta()
except Exception as exc:
    st.error(f'Error al cargar el modelo: {exc}')
    st.stop()

# ================================================================ Medir
st.markdown(ui.header(), unsafe_allow_html=True)
st.markdown('<div id="medir"></div>', unsafe_allow_html=True)

top_text, top_meter = st.columns([6, 5], gap='large')
with top_text:
    mode = st.radio('¿Cómo quieres ingresar tu consumo?', [MODE_APPLIANCES, MODE_WATTS], horizontal=True)
    if mode == MODE_WATTS:
        for key, val in WATT_DEFAULTS.items():
            st.session_state.setdefault(key, val)
        if REPLAY.exists():
            examples = load_replay()
            options = {'—': None}
            regular = examples.loc[examples['cluster'] >= 0]
            unusual = examples.loc[examples['cluster'] == -1]
            high = examples.loc[examples['Global_active_power'] > bundle['thresholds']['power_p95']]
            if len(regular):
                options['Ejemplo: consumo normal'] = regular.iloc[0]
            if len(high):
                options['Ejemplo: consumo alto'] = high.iloc[0]
            if len(unusual):
                options['Ejemplo: combinación rara'] = unusual.iloc[0]
            if len(options) > 1:
                pick = st.selectbox('¿Quieres probar con un ejemplo real?', list(options))
                if st.button('Usar este ejemplo') and options[pick] is not None:
                    s = to_simple(options[pick])
                    other = max(s['total_w'] - s['cocina_w'] - s['lavanderia_w'] - s['calentador_w'], 0)
                    st.session_state.update(
                        f_cocina=round(s['cocina_w']), f_lav=round(s['lavanderia_w']),
                        f_cal=round(s['calentador_w']), f_otros=round(other),
                    )
                    st.rerun()
    else:
        st.caption('Marca los aparatos que usaste en los últimos 30 minutos, dentro de cada habitación.')

with top_meter:
    with st.container(key='medidor'):
        meter_slot = st.empty()
        price_col, name_col = st.columns(2)
        price = price_col.number_input(
            'Precio del kWh (COP)', 0.0, 100000.0, step=50.0, value=DEFAULT_PRICE_COP,
            help='Valor ilustrativo; cámbialo por el de tu factura. Con 0 no se calcula el costo.',
        )
        etiqueta = name_col.text_input('Nombre de la consulta', placeholder='Ej: Domingo con la lavadora')
        go_top = st.button('Revisar mi consumo', type='primary', key='go_top')

result_slot = st.container()
roof_slot = st.empty()

catalog = load_appliances()
with st.container(key='casa'):
    row_top = st.columns(2)
    row_bottom = st.columns(2)
    layout = [('agua_aire', row_top[0]), ('otros', row_top[1]), ('cocina', row_bottom[0]), ('lavanderia', row_bottom[1])]
    zones = {}
    for zone, column in layout:
        with column:
            zones[zone] = room_card(zone, mode, catalog)
st.markdown('<div class="ew-ground"></div>', unsafe_allow_html=True)
go_bottom = st.button('Revisar mi consumo', type='primary', key='go_bottom')

total_w = sum(zones.values())
levels = {z: min(zones[z] / FULL_LIGHT_W[z], 1.0) for z in zones}
st.markdown(ui.glow_css(levels), unsafe_allow_html=True)
meter_slot.markdown(ui.meter_panel(meter_svg(total_w), total_w), unsafe_allow_html=True)

nivel = None
if go_top or go_bottom:
    with result_slot:
        nivel = check_consumption(zones, price, etiqueta)
roof_slot.markdown(roof_svg(nivel), unsafe_allow_html=True)

# ================================================================ Lecturas
st.markdown(
    ui.section('lecturas', 'Libro de lecturas', 'Tu historial', 'Cada consulta queda guardada para ver cómo cambia tu consumo.'),
    unsafe_allow_html=True,
)
history = db.list_measurements()
limits = bundle['thresholds']
if history.empty:
    st.info('Todavía no hay consultas. Haz una arriba o carga datos de ejemplo.')
else:
    m1, m2, m3 = st.columns(3)
    m1.metric('Consultas', len(history))
    m2.metric('Con alerta o revisión', int((history['nivel'] != 'normal').sum()))
    m3.metric('Consumo promedio', f"{history['Global_active_power'].mean() * 1000:,.0f} W")
    history['Consumo (W)'] = history['Global_active_power'] * 1000
    history['Estado'] = history['nivel'].map(lambda n: NIVELES[n][0])
    show_figure(ui.history_chart(history, limits['power_p05'], limits['power_p95']))
    with st.expander('Ver la tabla de consultas'):
        st.dataframe(
            history[['id', 'creado', 'etiqueta', 'Consumo (W)', 'Estado', 'mensaje']].rename(
                columns={'creado': 'Fecha', 'etiqueta': 'Nombre', 'mensaje': 'Detalle'}
            ),
            hide_index=True,
            width='stretch',
        )
d1, d2, d3, d4 = st.columns(4)
if not history.empty:
    d1.download_button(
        'Descargar CSV', history[db.COLUMNS].to_csv(index=False).encode('utf-8'), 'historial_energywatch.csv', 'text/csv'
    )
    with d2.popover('Borrar una consulta'):
        del_id = st.selectbox('Número (id)', history['id'])
        if st.button('Borrar'):
            db.delete_measurement(del_id)
            st.rerun()
    with d3.popover('Borrar todo'):
        st.write('Se eliminarán todas tus consultas.')
        if st.button('Sí, borrar todo'):
            db.clear_all()
            st.rerun()
with d4.popover('Datos de ejemplo'):
    st.write(
        'Agrega 40 consultas calculadas con ventanas reales del conjunto de prueba, '
        'repartidas en las últimas dos semanas y marcadas como ejemplo.'
    )
    if st.button('Agregar ejemplos'):
        seed(40)
        st.rerun()

# ================================================================ Un día real
st.markdown(
    ui.section(
        'dia', 'Reproducción', 'Un día de datos reales',
        'Ventanas históricas del conjunto de evaluación. No es un medidor conectado en vivo.',
    ),
    unsafe_allow_html=True,
)
if not REPLAY.exists():
    st.error('Falta data/processed/replay_test.csv. Vuelve a ejecutar el entrenamiento.')
else:
    replay = load_replay()
    n = st.slider('Cantidad de ventanas de 30 min', 5, 60, 20)
    subset = replay.head(n)
    if st.button('Reproducir', type='primary'):
        status, chart, table = st.empty(), st.empty(), st.empty()
        for i in range(len(subset)):
            cur = subset.iloc[i]
            status.markdown(
                f"<div class='ew-kicker'>{i + 1}/{n} · {cur['timestamp']}</div>**{cur['alert']}**",
                unsafe_allow_html=True,
            )
            fig = ui.replay_chart(subset.iloc[: i + 1], limits['power_p05'], limits['power_p95'])
            chart.pyplot(fig, clear_figure=True, width='stretch')
            ui.close(fig)
            table.dataframe(
                subset.iloc[: i + 1][['timestamp', 'Global_active_power', 'cluster', 'alert']].tail(6),
                hide_index=True,
                width='stretch',
            )
            time.sleep(0.05)

# ================================================================ Planos
st.markdown(
    ui.section('planos', 'Planos técnicos', 'Cómo funciona', 'El modelo, los datos y sus límites, sin letra chica.'),
    unsafe_allow_html=True,
)
info, test = meta['train_metrics'], meta['test_metrics']
cols = st.columns(4)
cols[0].metric('Clústeres', info['n_clusters'])
cols[1].metric('Ruido (entrenamiento)', f"{info['noise_ratio']:.1%}")
cols[2].metric(
    'Silhouette (prueba)', f"{test['silhouette_no_noise']:.3f}" if test['silhouette_no_noise'] is not None else 'No definida'
)
cols[3].metric('Ventanas válidas', f"{meta['total_windows']:,}")
st.markdown('#### Escenarios típicos de un hogar colombiano')
st.dataframe(
    pd.DataFrame([{'Escenario': n_, 'Desde (kW)': lo, 'Hasta (kW)': hi, 'Ejemplo': d} for n_, lo, hi, d in SCENARIOS]),
    hide_index=True,
    width='stretch',
)
if REPLAY.exists():
    st.markdown('#### Así se agrupan las ventanas reales')
    st.caption('Cada punto es una ventana de 30 minutos del conjunto de prueba. Las cruces son ruido: combinaciones poco habituales.')
    show_figure(ui.density_map(load_replay()))
st.markdown(
    '''**Datos de entrenamiento:** UCI *Individual Household Electric Power Consumption* (CC BY 4.0), una vivienda
medida minuto a minuto durante cuatro años (2.075.259 registros), agregada en ventanas de 30 minutos.

**La casa y el modelo:** tres habitaciones coinciden con los submedidores del dataset (cocina, lavandería y nevera, calentador de agua o aire) y la sala agrupa el resto.

**DBSCAN** agrupa observaciones próximas según densidad. `eps` define el radio y `min_samples` la densidad mínima. La etiqueta **-1** es ruido: una combinación poco habitual.

**Traducción de la entrada simple:** el usuario ingresa vatios (o aparatos del catálogo colombiano); la app los convierte a las 7 variables del dataset (kW, Wh/min = W/60, corriente = P/240 V, reactiva típica). Se usa el voltaje del entrenamiento (240 V) porque el modelo no vio redes de 120 V.

**Inferencia:** DBSCAN no tiene `predict()`; una entrada nueva toma el clúster del punto núcleo más cercano si está a distancia ≤ `eps`, o -1 si no. No reentrena el modelo.

**Consumo alto:** se compara contra el percentil 95 histórico de potencia, independiente del clúster.

**Evaluación:** división cronológica 80/20; el escalador se ajusta solo con entrenamiento.

**Limitación:** los datos de entrenamiento provienen de una sola vivienda extranjera; los hábitos colombianos (cocina a gas, ducha eléctrica) difieren. Por eso el resultado es orientativo. El catálogo de electrodomésticos colombianos (`data/reference/`) se usa solo para facilitar el ingreso, no para entrenar.

**Historial:** cada consulta se guarda en SQLite (`data/energywatch.db`).'''
)
with st.expander('Búsqueda de hiperparámetros (18 combinaciones)'):
    search = pd.DataFrame(meta['all_search_results']).rename(
        columns={
            'silhouette_no_noise': 'Silhouette',
            'noise_ratio': 'Ruido',
            'n_clusters': 'Clústeres',
            'min_cluster_size': 'Clúster mínimo',
        }
    )
    search['Elegida'] = (search['eps'] == meta['parameters']['eps']) & (
        search['min_samples'] == meta['parameters']['min_samples']
    )
    st.dataframe(search, hide_index=True, width='stretch')
st.markdown(
    '[Dataset original y licencia CC BY 4.0](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)'
)
