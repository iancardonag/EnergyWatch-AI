"""Entrenamiento y evaluación temporal de DBSCAN.

Ejecutar desde raíz: python -m src.train
"""

import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from src.preprocessing import FEATURES, download_dataset, load_windows, transform_features
from src.predict import assign_records, analyze_records


def summarize(labels, X, seed=42):
    unique = set(labels) - {-1}
    noise = float(np.mean(labels == -1))
    score = None
    selected = labels != -1
    sizes = pd.Series(labels[selected]).value_counts()
    # Silhouette definido para 2..n-1 etiquetas. Muestra acotada por coste.
    if 2 <= len(unique) < int(selected.sum()) and len(sizes) and sizes.min() >= 2:
        try:
            score = float(
                silhouette_score(
                    X[selected], labels[selected], sample_size=min(800, int(selected.sum())), random_state=seed
                )
            )
        except ValueError:
            pass
    return {
        'silhouette_no_noise': score,
        'noise_ratio': noise,
        'n_clusters': len(unique),
        'min_cluster_size': int(sizes.min()) if len(sizes) else 0,
    }


def split_windows(windows, n_train=3500, n_test=1200):
    """División cronológica 80/20 y muestreo reproducible (también usada por el notebook)."""
    # División cronológica; test nunca interviene en ajustar escalador o hiperparámetros.
    split = int(len(windows) * 0.8)
    train_pool, test_pool = windows.iloc[:split], windows.iloc[split:]
    # Muestreo reproducible dentro del segmento temporal de entrenamiento.
    train_df = train_pool.sample(n=min(n_train, len(train_pool)), random_state=42).sort_values('timestamp')
    test_df = test_pool.sample(n=min(n_test, len(test_pool)), random_state=43).sort_values('timestamp')
    return train_pool, test_pool, train_df, test_df


def train(raw='data/raw', n_train=3500, n_test=1200):
    path = download_dataset(raw)
    windows = load_windows(path)
    if len(windows) < 500:
        raise ValueError('Menos de 500 ventanas válidas; revisar datos')
    train_pool, test_pool, train_df, test_df = split_windows(windows, n_train, n_test)
    X_train, scaler = transform_features(train_df)
    X_test, _ = transform_features(test_df, scaler)
    candidates = []
    best = None
    for eps in [0.35, 0.5, 0.7, 0.9, 1.1, 1.4]:
        for minimum in [8, 15, 25]:
            model = DBSCAN(eps=eps, min_samples=minimum, n_jobs=-1).fit(X_train)
            metrics = summarize(model.labels_, X_train)
            record = {'eps': eps, 'min_samples': minimum, **metrics}
            candidates.append(record)
            # Evitar triviales: 2+ clusters, ruido máximo 45%, grupos de al menos 1%.
            if (
                metrics['silhouette_no_noise'] is not None
                and metrics['n_clusters'] >= 2
                and metrics['noise_ratio'] <= 0.45
                and metrics['min_cluster_size'] >= max(5, int(len(train_df) * 0.01))
            ):
                rank = metrics['silhouette_no_noise'] - 0.2 * metrics['noise_ratio']
                if best is None or rank > best[0]:
                    best = (rank, model, record)
    if best is None:
        # Persistir diagnóstico experimental, no publicar un modelo no validado como exitoso.
        Path('models').mkdir(exist_ok=True)
        Path('models/search_results.json').write_text(json.dumps(candidates, indent=2), encoding='utf-8')
        raise RuntimeError(
            'Ninguna combinación produjo >=2 clústeres suficientemente representativos. Revisar models/search_results.json; no se fabrican resultados.'
        )
    _, model, train_metrics = best
    core_indices = model.core_sample_indices_
    thresholds = {
        'power_p95': float(train_pool['Global_active_power'].quantile(0.95)),
        'power_p05': float(train_pool['Global_active_power'].quantile(0.05)),
    }
    bundle = {
        'scaler': scaler,
        'model': model,
        'core_points': model.components_,
        'core_labels': model.labels_[core_indices].astype(int),
        'eps': float(model.eps),
        'features': FEATURES,
        'thresholds': thresholds,
        'window': '30min',
        'version': '1.0',
    }
    # Validación temporal usando una regla de asignación explícita (no DBSCAN predict).
    test_labels = assign_records(test_df, bundle)['cluster'].to_numpy()
    test_metrics = summarize(test_labels, X_test, seed=43)
    out = Path('models')
    out.mkdir(exist_ok=True)
    joblib.dump(bundle, out / 'modelo.joblib', compress=3)
    meta = {
        'dataset': 'UCI Individual Household Electric Power Consumption',
        'source': 'https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption',
        'total_windows': len(windows),
        'train_pool': len(train_pool),
        'test_pool': len(test_pool),
        'train_used': len(train_df),
        'test_used': len(test_df),
        'train_metrics': train_metrics,
        'test_metrics': test_metrics,
        'all_search_results': candidates,
        'parameters': {'eps': model.eps, 'min_samples': model.min_samples},
        'thresholds': thresholds,
        'method': 'core nearest neighbor assignment, held-out chronological split',
        'warning': 'Silhouette excluye ruido; leer junto con noise_ratio. Puntuacion de test es solo descriptiva.',
    }
    (out / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    replay = analyze_records(test_df, bundle)
    replay.to_csv('data/processed/replay_test.csv', index=False)
    print(json.dumps({k: v for k, v in meta.items() if k != 'all_search_results'}, indent=2, ensure_ascii=False))
    return meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', default='data/raw')
    ap.add_argument('--n-train', type=int, default=3500)
    ap.add_argument('--n-test', type=int, default=1200)
    args = ap.parse_args()
    train(args.raw, args.n_train, args.n_test)
