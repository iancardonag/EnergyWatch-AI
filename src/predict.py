"""Asignación fuera de muestra a núcleos DBSCAN: no es predict() nativo."""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from src.preprocessing import FEATURES, transform_features


def assign_records(frame, bundle):
    transformed, _ = transform_features(frame, bundle['scaler'])
    core = bundle['core_points']
    if len(core) == 0:
        raise ValueError('Modelo sin puntos núcleo')
    nn = NearestNeighbors(n_neighbors=1, metric='euclidean').fit(core)
    dist, indices = nn.kneighbors(transformed)
    dist = dist.ravel()
    labels = np.where(dist <= bundle['eps'], bundle['core_labels'][indices.ravel()], -1)
    result = frame.copy()
    result['cluster'] = labels.astype(int)
    result['core_distance'] = dist
    result['statistical_outlier'] = labels == -1
    return result


def analyze_records(frame, bundle):
    """Alerta de negocio independiente del agrupamiento, basada en percentiles train."""
    result = assign_records(frame, bundle)
    thresholds = bundle['thresholds']
    power = result['Global_active_power'].to_numpy()
    hi = power > thresholds['power_p95']
    lo = power < thresholds['power_p05']
    labels = np.where(
        hi,
        'Potencia elevada frente a referencia histórica',
        np.where(lo, 'Potencia baja frente a referencia histórica', 'Potencia dentro de referencias históricas'),
    )
    result['power_status'] = labels
    result['alert'] = np.where(
        result['statistical_outlier'] & hi,
        'Patrón atípico y potencia elevada',
        np.where(
            result['statistical_outlier'] & lo,
            'Patrón atípico y potencia baja',
            np.where(
                result['statistical_outlier'],
                'Combinación eléctrica atípica',
                np.where(hi, 'Patrón conocido con potencia elevada', 'Patrón conocido'),
            ),
        ),
    )
    return result
