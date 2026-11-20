import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from src.preprocessing import FEATURES, transform_features
from src.predict import analyze_records


def test_inference_to_core_and_outlier():
    # Datos artificiales usados únicamente para pruebas unitarias, nunca para entrenamiento del proyecto.
    base = np.array([1, 0.1, 230, 5, 2, 1, 3], dtype=float)
    rng = np.random.default_rng(2)
    train = pd.DataFrame(base + rng.normal(0, 0.008, (80, 7)), columns=FEATURES)
    x, scaler = transform_features(train)
    model = DBSCAN(eps=4.0, min_samples=4).fit(x)
    bundle = {
        'scaler': scaler,
        'core_points': model.components_,
        'core_labels': model.labels_[model.core_sample_indices_],
        'eps': model.eps,
        'thresholds': {'power_p05': 0.5, 'power_p95': 3},
    }
    same = analyze_records(train.iloc[[0]], bundle)
    assert int(same.iloc[0]['cluster']) >= 0
    far = pd.DataFrame([[10, 2, 280, 40, 80, 60, 70]], columns=FEATURES)
    result = analyze_records(far, bundle)
    assert int(result.iloc[0]['cluster']) == -1
    assert 'elevada' in result.iloc[0]['alert']
