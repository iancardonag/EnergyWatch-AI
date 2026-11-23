"""EnergyWatch AI: revisa si el consumo de tu hogar es normal (DBSCAN + historial en SQLite)."""

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
from src.simple_input import from_simple, to_simple, zones_exceed_total
from src.advice import NIVELES, verdict, tips, daily_cost
from src.catalog import (
    DEFAULT_PRICE_COP,
    SCENARIOS,
    ZONE_LABELS,
    describe_scenario,
    load_catalog,
    totals_from_appliances,
)
from src import database as db
from src import ui
from src.house import house_svg, zones_from_watts
from src.seed_demo import seed

st.set_page_config(page_title='EnergyWatch AI', page_icon=str(ROOT / 'app' / 'static' / 'icon.png'), layout='wide')
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown(ui.header(), unsafe_allow_html=True)

REPLAY = ROOT / 'data' / 'processed' / 'replay_test.csv'
WINDOW_MINUTES = 30  # el modelo analiza ventanas de 30 minutos
MODE_APPLIANCES = 'Elegir mis electrodomésticos'
MODE_WATTS = 'Ya conozco mis vatios'


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


def check_consumption(total_w, cocina_w, lavanderia_w, agua_aire_w, price, etiqueta):
    """Evalúa el consumo con el modelo, muestra el resultado y lo guarda en el historial."""
    if total_w <= 0:
        st.error('El consumo total debe ser mayor que 0 W. Marca al menos un aparato o escribe un valor.')
        return None
    if zones_exceed_total(total_w, cocina_w, lavanderia_w, agua_aire_w):
        st.warning('La suma de cocina, lavandería y ducha/aire supera el total de la casa. Revisa los valores.')
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


if not (ROOT / 'models' / 'modelo.joblib').exists():
    st.warning('Aún falta entrenar el modelo. Ejecuta estos comandos en la carpeta del proyecto:')
    st.code('pip install -r requirements.txt\npython -m src.train\nstreamlit run app/app.py')
    st.stop()

try:
    bundle, meta = load_model(), load_meta()
except Exception as exc:
    st.error(f'Error al cargar el modelo: {exc}')
    st.stop()

tabs = st.tabs(['Inicio', 'Revisar mi consumo', 'Mi historial', 'Demostración', 'Cómo funciona'])

# ---------------------------------------------------------------- Inicio
with tabs[0]:
    art, text = st.columns([6, 5], gap='large')
    resting = {'cocina': 0, 'lavanderia': 175, 'agua_aire': 0, 'otros': 120}
    art.markdown(
        ui.plate(house_svg(resting, nivel='normal'), 'Casa en reposo · nevera y luces: lectura habitual'),
        unsafe_allow_html=True,
    )
    steps = [
        ('1.', 'Cuéntanos qué usas', 'Marca tus electrodomésticos en cada habitación o escribe tus vatios.'),
        ('2.', 'Mira cómo se ilumina la casa', 'Cada habitación brilla según lo que consume, y el medidor marca el total.'),
        ('3.', 'Recibe el sello', 'Habitual, revisar o alerta, con el costo por día y consejos para ahorrar.'),
    ]
    text.markdown(ui.steps(steps), unsafe_allow_html=True)
    history = db.list_measurements()
    m1, m2, m3 = text.columns(3)
    m1.metric('Consultas', len(history))
    m2.metric('Con alerta', int((history['nivel'] != 'normal').sum()) if len(history) else 0)
    m3.metric('Promedio', f"{history['Global_active_power'].mean() * 1000:,.0f} W" if len(history) else '—')
    st.write('')
    st.markdown('#### Qué es un consumo típico en un hogar colombiano')
    st.dataframe(
        pd.DataFrame([{'Escenario': n, 'Desde (kW)': lo, 'Hasta (kW)': hi, 'Ejemplo': d} for n, lo, hi, d in SCENARIOS]),
        hide_index=True,
        width='stretch',
    )
    st.caption(
        'Herramienta orientativa: compara tu consumo con miles de mediciones reales de un hogar. '
        'No diagnostica fallas eléctricas ni reemplaza a un técnico certificado.'
    )

# ---------------------------------------------------------------- Revisar
with tabs[1]:
    house_col, form_col = st.columns([5, 6], gap='large')
    house_slot = house_col.empty()
    house_zones = {'cocina': 0, 'lavanderia': 0, 'agua_aire': 0, 'otros': 0}
    house_total, house_nivel = 0.0, None
    with form_col:
        st.markdown('<div class="ew-kicker">Paso 1 · Ingreso de datos</div>', unsafe_allow_html=True)
        st.write('El análisis usa el consumo **promedio de una ventana de 30 minutos**.')
        mode = st.radio('¿Cómo quieres ingresar tu consumo?', [MODE_APPLIANCES, MODE_WATTS], horizontal=True)
        left, right = st.columns([2, 1])
        etiqueta = left.text_input('Nombre de esta consulta (opcional)', placeholder='Ej: Domingo con la lavadora')
        price = right.number_input(
            'Precio de tu kWh (COP)',
            0.0,
            100000.0,
            step=50.0,
            value=DEFAULT_PRICE_COP,
            help='Valor ilustrativo; cámbialo por el de tu factura. Con 0 no se calcula el costo.',
        )

        if mode == MODE_APPLIANCES:
            st.write(
                '**Marca** los aparatos que usaste en los últimos 30 minutos, y elige **cuántos** son y '
                '**cuántos minutos** estuvieron encendidos.'
            )
            catalog = load_appliances()
            rows = []
            for zone, label in ZONE_LABELS.items():
                with st.expander(label, expanded=zone != 'otros'):
                    for _, item in catalog[catalog['zona'] == zone].iterrows():
                        name = item['aparato']
                        col_name, col_qty, col_min = st.columns([3, 1, 1])
                        used = col_name.checkbox(f"{name} ({item['potencia_tipica_w']:.0f} W)", key=f'use_{name}')
                        qty = col_qty.number_input(
                            'Cantidad', 1, 10, 1, key=f'qty_{name}', disabled=not used, label_visibility='collapsed'
                        )
                        mins = col_min.number_input(
                            'Minutos',
                            1,
                            WINDOW_MINUTES,
                            WINDOW_MINUTES,
                            step=1,
                            key=f'min_{name}',
                            disabled=not used,
                            label_visibility='collapsed',
                            help=f'Minutos encendido de los últimos {WINDOW_MINUTES}',
                        )
                        rows.append(
                            {
                                'potencia_tipica_w': item['potencia_tipica_w'],
                                'zona': zone,
                                'cantidad': qty if used else 0,
                                'minutos': mins,
                            }
                        )
            sums = totals_from_appliances(pd.DataFrame(rows))
            house_zones = {z: sums[z] for z in house_zones}
            house_total = sums['total_w']
            st.metric('Consumo promedio estimado', f"{sums['total_w']:,.0f} W")
            if st.button('Revisar mi consumo', type='primary', key='go_appliances'):
                house_nivel = check_consumption(
                    sums['total_w'], sums['cocina'], sums['lavanderia'], sums['agua_aire'], price, etiqueta
                )
        else:
            defaults = {'f_total': 1200.0, 'f_cocina': 130.0, 'f_lav': 0.0, 'f_cal': 600.0}
            for key, val in defaults.items():
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
                        st.session_state.update(
                            f_total=round(s['total_w']),
                            f_cocina=round(s['cocina_w']),
                            f_lav=round(s['lavanderia_w']),
                            f_cal=round(s['calentador_w']),
                        )
                        st.rerun()
            with st.form('consulta'):
                total_w = st.number_input('Consumo total de la casa (W)', 0.0, 50000.0, step=50.0, key='f_total')
                a, b, c = st.columns(3)
                cocina_w = a.number_input(
                    'Cocina (W)',
                    0.0,
                    6000.0,
                    step=10.0,
                    key='f_cocina',
                    help='Horno, microondas, airfryer… (máximo típico 6.000 W)',
                )
                lav_w = b.number_input('Lavandería, nevera y luces (W)', 0.0, 6000.0, step=10.0, key='f_lav')
                cal_w = c.number_input(
                    'Ducha, calentador o aire (W)',
                    0.0,
                    11000.0,
                    step=10.0,
                    key='f_cal',
                    help='Máximo típico 11.000 W si coinciden dos aparatos',
                )
                submitted = st.form_submit_button('Revisar mi consumo', type='primary')
            house_total = total_w
            house_zones = zones_from_watts(total_w, cocina_w, lav_w, cal_w)
            if submitted:
                house_nivel = check_consumption(total_w, cocina_w, lav_w, cal_w, price, etiqueta)


    house_slot.markdown(
        ui.plate(
            house_svg(house_zones, house_total, house_nivel),
            'Tu casa · se ilumina con lo que marcas' if house_nivel is None else 'Tu casa · lectura de esta consulta',
        ),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- Historial
with tabs[2]:
    history = db.list_measurements()
    if history.empty:
        st.info('Todavía no hay consultas. Haz una en **Revisar mi consumo** o carga datos de ejemplo.')
    else:
        history['Consumo (W)'] = history['Global_active_power'] * 1000
        history['Estado'] = history['nivel'].map(lambda n: NIVELES[n][0])
        limits = bundle['thresholds']
        show_figure(ui.history_chart(history, limits['power_p05'], limits['power_p95']))
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
            'Descargar CSV',
            history[db.COLUMNS].to_csv(index=False).encode('utf-8'),
            'historial_energywatch.csv',
            'text/csv',
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

# ---------------------------------------------------------------- Demostración
with tabs[3]:
    st.info('Reproduce mediciones históricas reales del conjunto de evaluación. No es un medidor conectado en vivo.')
    if not REPLAY.exists():
        st.error('Falta data/processed/replay_test.csv. Vuelve a ejecutar el entrenamiento.')
    else:
        replay = load_replay()
        n = st.slider('Cantidad de ventanas de 30 min', 5, 60, 20)
        subset = replay.head(n)
        limits = bundle['thresholds']
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

# ---------------------------------------------------------------- Cómo funciona
with tabs[4]:
    info, test = meta['train_metrics'], meta['test_metrics']
    cols = st.columns(4)
    cols[0].metric('Clústeres', info['n_clusters'])
    cols[1].metric('Ruido (entrenamiento)', f"{info['noise_ratio']:.1%}")
    cols[2].metric(
        'Silhouette (prueba)', f"{test['silhouette_no_noise']:.3f}" if test['silhouette_no_noise'] is not None else 'No definida'
    )
    cols[3].metric('Ventanas válidas', f"{meta['total_windows']:,}")
    if REPLAY.exists():
        st.markdown('#### Así se agrupan las ventanas reales')
        st.caption('Cada punto es una ventana de 30 minutos del conjunto de prueba. Las cruces rojas son ruido: combinaciones poco habituales.')
        show_figure(ui.density_map(load_replay()))
    st.markdown(
        '''**Datos de entrenamiento:** UCI *Individual Household Electric Power Consumption* (CC BY 4.0), una vivienda
medida minuto a minuto durante cuatro años (2.075.259 registros), agregada en ventanas de 30 minutos.

**DBSCAN** agrupa observaciones próximas según densidad. `eps` define el radio y `min_samples` la densidad mínima. La etiqueta **-1** es ruido: una combinación poco habitual.

**Traducción de la entrada simple:** el usuario ingresa vatios (o aparatos del catálogo colombiano); la app los convierte a las 7 variables del dataset (kW, Wh/min = W/60, corriente = P/240 V, reactiva típica). Se usa el voltaje del entrenamiento (240 V) porque el modelo no vio redes de 120 V.

**Inferencia:** DBSCAN no tiene `predict()`; una entrada nueva toma el clúster del punto núcleo más cercano si está a distancia ≤ `eps`, o -1 si no. No reentrena el modelo.

**Consumo alto:** se compara contra el percentil 95 histórico de potencia, independiente del clúster.

**Evaluación:** división cronológica 80/20; el escalador se ajusta solo con entrenamiento.

**Limitación:** los datos de entrenamiento provienen de una sola vivienda extranjera; los hábitos colombianos (cocina a gas, ducha eléctrica) difieren. Por eso el resultado es orientativo. El catálogo de electrodomésticos colombianos (`data/reference/`) se usa solo para facilitar el ingreso, no para entrenar.

**Historial:** cada consulta se guarda en SQLite (`data/energywatch.db`).'''
    )
    st.markdown('#### Búsqueda de hiperparámetros')
    search = pd.DataFrame(meta['all_search_results']).rename(
        columns={
            'eps': 'eps',
            'min_samples': 'min_samples',
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
