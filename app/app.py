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

st.set_page_config(page_title='EnergyWatch AI', page_icon='⚡', layout='wide')
st.title('⚡ EnergyWatch AI')
st.caption('Descubre si el consumo de electricidad de tu hogar es normal · guarda tu historial')

REPLAY = ROOT / 'data' / 'processed' / 'replay_test.csv'
WINDOW_MINUTES = 30  # el modelo analiza ventanas de 30 minutos


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


def check_consumption(total_w, cocina_w, lavanderia_w, agua_aire_w, price, etiqueta):
    """Evalúa el consumo con el modelo, muestra el resultado y lo guarda en el historial."""
    if total_w <= 0:
        st.error('El consumo total debe ser mayor que 0 W. Marca al menos un aparato o escribe un valor.')
        return
    if zones_exceed_total(total_w, cocina_w, lavanderia_w, agua_aire_w):
        st.warning('La suma de cocina, lavandería y ducha/aire supera el total de la casa. Revisa los valores.')
    try:
        values = from_simple(total_w, cocina_w, lavanderia_w, agua_aire_w)
        result = analyze_records(pd.DataFrame([values]), bundle).iloc[0]
        nivel, mensaje = verdict(result)
        icon, titulo = NIVELES[nivel]
        box = {'normal': st.success, 'atencion': st.warning, 'alto': st.error}[nivel]
        box(f'{icon} **{titulo}** — {mensaje}')
        st.markdown(describe_scenario(total_w / 1000))
        kwh, cost = daily_cost(total_w, price)
        k1, k2 = st.columns(2)
        k1.metric('Si se mantuviera todo el día', f'{kwh:.1f} kWh')
        if price > 0:
            k2.metric('Costo estimado por día', f'${cost:,.0f} COP')
        st.markdown('**Qué puedes hacer**')
        for tip in tips(total_w, cocina_w, lavanderia_w, agua_aire_w, nivel):
            st.markdown(f'- {tip}')
        db.save_measurement(values, result, nivel, mensaje, etiqueta)
        st.caption('✅ Consulta guardada en tu historial. Es orientativa: no confirma fallas ni riesgos eléctricos.')
    except Exception as exc:
        st.error(f'No fue posible revisar el consumo: {exc}')


if not (ROOT / 'models' / 'modelo.joblib').exists():
    st.warning('Aún falta entrenar el modelo. Ejecuta estos comandos en la carpeta del proyecto:')
    st.code('pip install -r requirements.txt\npython -m src.train\nstreamlit run app/app.py')
    st.stop()

try:
    bundle, meta = load_model(), load_meta()
except Exception as exc:
    st.error(f'Error al cargar el modelo: {exc}')
    st.stop()

tabs = st.tabs(['🏠 Inicio', '🔎 Revisar mi consumo', '📒 Mi historial', '▶️ Demostración', '🧠 Cómo funciona'])

# ---------------------------------------------------------------- Inicio
with tabs[0]:
    st.subheader('¿Es normal el consumo de mi casa?')
    st.write(
        'Elige los electrodomésticos que tienes encendidos (o escribe los **vatios** de tu casa) y te digo '
        'si ese consumo es habitual, junto con consejos para ahorrar.'
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown('### 1️⃣ Elige\nMarca tus electrodomésticos y cuántos minutos estuvieron encendidos.')
    c2.markdown('### 2️⃣ Recibe\nUn semáforo 🟢🟡🔴, una explicación sencilla y consejos para ahorrar.')
    c3.markdown('### 3️⃣ Compara\nCada consulta se guarda en **Mi historial** para ver cómo cambia tu consumo.')
    history = db.list_measurements()
    m1, m2, m3 = st.columns(3)
    m1.metric('Consultas guardadas', len(history))
    m2.metric('Con alerta', int((history['nivel'] != 'normal').sum()) if len(history) else 0)
    m3.metric('Consumo promedio', f"{history['Global_active_power'].mean() * 1000:,.0f} W" if len(history) else '—')
    st.markdown('#### ¿Qué es un consumo típico en un hogar colombiano?')
    st.dataframe(
        pd.DataFrame(
            [{'Escenario': n, 'Desde (kW)': lo, 'Hasta (kW)': hi, 'Ejemplo': d} for n, lo, hi, d in SCENARIOS]
        ),
        hide_index=True,
        width='stretch',
    )
    st.info(
        'Herramienta orientativa: compara tu consumo con un historial de miles de mediciones reales de hogares. '
        'No diagnostica fallas eléctricas ni reemplaza a un técnico certificado.'
    )

# ---------------------------------------------------------------- Revisar
with tabs[1]:
    st.subheader('Revisar mi consumo')
    st.write('El análisis usa el consumo **promedio de una ventana de 30 minutos**.')
    mode = st.radio(
        '¿Cómo quieres ingresar tu consumo?',
        ['🔌 Elegir mis electrodomésticos', '⚡ Ya conozco mis vatios'],
        horizontal=True,
    )
    etiqueta = st.text_input('Nombre de esta consulta (opcional)', placeholder='Ej: Domingo con la lavadora')
    price = st.number_input(
        '💲 Precio de tu kWh (COP)',
        0.0,
        100000.0,
        step=50.0,
        value=DEFAULT_PRICE_COP,
        help='Valor ilustrativo; cámbialo por el de tu factura. Con 0 no se calcula el costo.',
    )

    if mode.startswith('🔌'):
        st.write(
            '**Marca** los aparatos que usaste en los últimos 30 minutos, y elige **cuántos** son y '
            '**cuántos minutos** estuvieron encendidos.'
        )
        catalog = load_appliances()
        rows = []
        for zone, label in ZONE_LABELS.items():
            with st.expander(label, expanded=True):
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
        st.metric('Consumo promedio estimado', f"{sums['total_w']:,.0f} W")
        if st.button('Revisar mi consumo', type='primary', key='go_appliances'):
            check_consumption(sums['total_w'], sums['cocina'], sums['lavanderia'], sums['agua_aire'], price, etiqueta)
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
            total_w = st.number_input('🏠 Consumo total de la casa (W)', 0.0, 50000.0, step=50.0, key='f_total')
            a, b, c = st.columns(3)
            cocina_w = a.number_input(
                '🍳 Cocina (W)',
                0.0,
                6000.0,
                step=10.0,
                key='f_cocina',
                help='Horno, microondas, airfryer… (máximo típico 6.000 W)',
            )
            lav_w = b.number_input('🧺 Lavandería, nevera y luces (W)', 0.0, 6000.0, step=10.0, key='f_lav')
            cal_w = c.number_input(
                '🔥 Ducha / calentador / aire (W)',
                0.0,
                11000.0,
                step=10.0,
                key='f_cal',
                help='Máximo típico 11.000 W si coinciden dos aparatos',
            )
            submitted = st.form_submit_button('Revisar mi consumo', type='primary')
        if submitted:
            check_consumption(total_w, cocina_w, lav_w, cal_w, price, etiqueta)

# ---------------------------------------------------------------- Historial
with tabs[2]:
    st.subheader('Mi historial')
    history = db.list_measurements()
    if history.empty:
        st.info('Todavía no hay consultas. Haz una en **Revisar mi consumo** y aparecerá aquí.')
    else:
        history['Consumo (W)'] = history['Global_active_power'] * 1000
        history['Estado'] = history['nivel'].map(lambda n: f'{NIVELES[n][0]} {NIVELES[n][1]}')
        st.line_chart(history.sort_values('creado').set_index('creado')['Consumo (W)'], height=220)
        st.dataframe(
            history[['id', 'creado', 'etiqueta', 'Consumo (W)', 'Estado', 'mensaje']].rename(
                columns={'creado': 'Fecha', 'etiqueta': 'Nombre', 'mensaje': 'Detalle'}
            ),
            hide_index=True,
            width='stretch',
        )
        d1, d2, d3 = st.columns([2, 1, 1])
        d1.download_button(
            '⬇️ Descargar historial (CSV)',
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

# ---------------------------------------------------------------- Demostración
with tabs[3]:
    st.subheader('Demostración con datos reales')
    st.info('Reproduce mediciones históricas reales del conjunto de evaluación. No es un medidor conectado en vivo.')
    if not REPLAY.exists():
        st.error('Falta data/processed/replay_test.csv. Vuelve a ejecutar el entrenamiento.')
    else:
        replay = load_replay()
        n = st.slider('Cantidad de ventanas de 30 min', 5, 60, 20)
        subset = replay.head(n)
        if st.button('▶️ Reproducir'):
            status, chart, table = st.empty(), st.empty(), st.empty()
            for i in range(len(subset)):
                cur = subset.iloc[i]
                status.info(f"{i + 1}/{n} · {cur['timestamp']} · {cur['alert']}")
                chart.line_chart(subset.iloc[: i + 1].set_index('timestamp')['Global_active_power'], height=190)
                table.dataframe(
                    subset.iloc[: i + 1][['timestamp', 'Global_active_power', 'cluster', 'alert']].tail(6),
                    hide_index=True,
                    width='stretch',
                )
                time.sleep(0.12)

# ---------------------------------------------------------------- Cómo funciona
with tabs[4]:
    st.subheader('Cómo funciona (detalle técnico)')
    info = meta['train_metrics']
    cols = st.columns(4)
    cols[0].metric('Clústeres', info['n_clusters'])
    cols[1].metric('Ruido', f"{info['noise_ratio']:.1%}")
    cols[2].metric(
        'Silhouette', f"{info['silhouette_no_noise']:.3f}" if info['silhouette_no_noise'] is not None else 'No definida'
    )
    cols[3].metric('Ventanas válidas', f"{meta['total_windows']:,}")
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
    st.json(
        {
            'params': meta['parameters'],
            'train': meta['train_metrics'],
            'test': meta['test_metrics'],
            'thresholds_kW': meta['thresholds'],
        }
    )
    st.markdown(
        '[Dataset original y licencia CC BY 4.0](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)'
    )
