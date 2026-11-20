# Arquitectura EnergyWatch AI

```mermaid
flowchart TD
    A[Dataset real UCI] --> B[Lectura y control de faltantes]
    B --> C[Ventanas de 30 minutos]
    C --> D[Split cronológico 80/20]
    D --> E[log1p y RobustScaler]
    E --> F[DBSCAN + selección eps y min_samples]
    F --> G[models/modelo.joblib + metadata.json]
    G --> H[Streamlit app/app.py]
    X[Excel electrodomésticos Colombia] --> Y[Catálogo CSV]
    Y --> H
    H --> I[Usuario elige aparatos o vatios]
    I --> J[simple_input: vatios a 7 variables]
    J --> K[predict: núcleo más cercano + percentiles]
    K --> L[advice: semáforo y consejos]
    L --> M[(SQLite: historial)]
    M --> H
```

**Capas:** presentación (`app/app.py`), lógica de negocio (`src/simple_input.py`, `src/advice.py`, `src/catalog.py`), modelo (`src/preprocessing.py`, `src/train.py`, `src/predict.py`) y persistencia (`src/database.py`).

No hay sensores en tiempo real: la pestaña Demostración reproduce mediciones históricas de prueba.
