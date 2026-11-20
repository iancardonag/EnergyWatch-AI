"""Preparación temporal y transformación determinista de mediciones de UCI."""

from pathlib import Path
import zipfile
import urllib.request
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

URL = 'https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip'
FEATURES = [
    'Global_active_power',
    'Global_reactive_power',
    'Voltage',
    'Global_intensity',
    'Sub_metering_1',
    'Sub_metering_2',
    'Sub_metering_3',
]
LOG_COLUMNS = [c for c in FEATURES if c != 'Voltage']


def download_dataset(raw_dir='data/raw'):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / 'household_power_consumption.txt'
    if dest.exists():
        return dest
    archive = raw_dir / 'household_power_consumption.zip'
    if not archive.exists():
        try:
            urllib.request.urlretrieve(URL, archive)
        except Exception as exc:
            raise RuntimeError(
                f'No se pudo descargar UCI. Descargar manualmente desde {URL} y colocar household_power_consumption.txt en {raw_dir}'
            ) from exc
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.endswith('household_power_consumption.txt')]
        if not names:
            raise ValueError('El ZIP no contiene el archivo esperado')
        with z.open(names[0]) as source, dest.open('wb') as target:
            import shutil

            shutil.copyfileobj(source, target)
    return dest


def load_windows(path, interval='30min'):
    """Ventanas sin datos inventados: promedio de mediciones válidas por 30 minutos.

    Se exige >=80% de cobertura por ventana; sin interpolación.
    Sub_metering_* se promedia como Wh/min, NO se interpreta como energía
    total de 30 min. El formulario debe ingresar valores medios de ventana.
    """
    df = pd.read_csv(path, sep=';', na_values=['?', ''], low_memory=False)
    expected = {'Date', 'Time', *FEATURES}
    if not expected.issubset(df.columns):
        raise ValueError(f'Columnas faltantes: {expected-set(df.columns)}')
    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    for feature in FEATURES:
        df[feature] = pd.to_numeric(df[feature], errors='coerce')
    df = df.dropna(subset=['timestamp']).sort_values('timestamp').drop_duplicates('timestamp')
    df = df.set_index('timestamp')
    # No se combinan componentes con cobertura diferente.
    counts = df[FEATURES].resample(interval).count()
    means = df[FEATURES].resample(interval).mean()
    expected_per_window = int(pd.Timedelta(interval) / pd.Timedelta(minutes=1))
    complete = counts.ge(int(np.ceil(0.8 * expected_per_window))).all(axis=1)
    out = means.loc[complete].dropna().reset_index()
    return out


def validate_frame(frame):
    if any(x not in frame.columns for x in FEATURES):
        raise ValueError('Faltan columnas eléctricas')
    x = frame[FEATURES].astype(float)
    if not np.isfinite(x.to_numpy()).all():
        raise ValueError('No se admiten valores vacíos ni infinitos')
    if (x[LOG_COLUMNS] < 0).any().any() or (x['Voltage'] <= 0).any():
        raise ValueError('Potencias, intensidad y submediciones >=0; voltaje > 0')
    return x


def transform_features(frame, scaler=None):
    x = validate_frame(frame).copy()
    x[LOG_COLUMNS] = np.log1p(x[LOG_COLUMNS])
    if scaler is None:
        scaler = RobustScaler().fit(x)
    return scaler.transform(x), scaler
