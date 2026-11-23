# ⚡ EnergyWatch AI — ¿Es normal el consumo de electricidad de mi hogar?

Aplicación web que usa **DBSCAN** (aprendizaje no supervisado) para decir, en lenguaje sencillo, si el consumo eléctrico de un hogar es habitual o poco común, con consejos de ahorro y un historial de consultas guardado en una base de datos SQLite. Proyecto de la Actividad 3 de Inteligencia Artificial I (despliegue de modelos de ML en la nube).

## Descripción

Muchas familias reciben la factura de energía sin saber si su consumo es normal. EnergyWatch AI permite elegir los electrodomésticos que están encendidos (catálogo con 29 aparatos típicos de Colombia: nevera, ducha eléctrica, lavadora, airfryer, etc.) o escribir los vatios de la casa, y responde con un semáforo 🟢🟡🔴, una explicación, el costo estimado por día en pesos (COP) y consejos para ahorrar. Cada consulta queda guardada en **Mi historial**, donde se puede ver la evolución y descargar un CSV.

No es un sistema de seguridad ni diagnostica fallas eléctricas: una combinación "atípica" es estadística, no una avería.

## Demostración

🔗 **Aplicación desplegada:** _[pegar aquí la URL pública de Streamlit Community Cloud]_

## Algoritmo utilizado

**DBSCAN** (`sklearn.cluster.DBSCAN`) agrupa observaciones por **densidad**: un punto pertenece a un clúster si tiene suficientes vecinos cercanos (`min_samples`) dentro de un radio (`eps`); los puntos aislados se etiquetan `-1` (ruido).

**Por qué es apropiado:** (1) el número de patrones de consumo no se conoce de antemano y DBSCAN no exige fijarlo; (2) los hogares tienen hábitos densos y repetidos, y nos interesan precisamente las combinaciones que no encajan, que DBSCAN marca de forma natural como ruido; (3) detecta clústeres de forma arbitraria, no solo esféricos como K-means.

**Entrenamiento:** ventanas de 30 min → `log1p` en potencias → `RobustScaler` ajustado solo con entrenamiento → búsqueda en malla de 18 combinaciones (`eps` ∈ {0.35, 0.5, 0.7, 0.9, 1.1, 1.4}, `min_samples` ∈ {8, 15, 25}) eligiendo la mayor `Silhouette − 0.2·ruido`, con al menos 2 clústeres, máximo 45 % de ruido y clústeres de al menos 1 % de los datos.

**Resultados reales** (`models/metadata.json`), con división **cronológica 80/20** (se entrena con el pasado y se evalúa con el futuro):

| Conjunto | Clústeres | Silhouette (sin ruido) | Ruido |
|---|---|---|---|
| Entrenamiento (3.500 ventanas) | 2 | **0,573** | 5,1 % |
| Prueba posterior (1.200 ventanas) | 2 | **0,618** | 2,9 % |

Parámetros elegidos: `eps = 1.1`, `min_samples = 15`. El mínimo exigido por la rúbrica es Silhouette > 0,4. Silhouette excluye los puntos de ruido, por eso se informa junto con su porcentaje.

**Inferencia:** DBSCAN no tiene `predict()`. Se guardan los puntos núcleo y una medición nueva toma el clúster del núcleo más cercano si está a distancia ≤ `eps`; de lo contrario es ruido (`-1`). Además se compara la potencia con los percentiles 5 y 95 históricos (0,21 kW y 3,07 kW) para avisar de consumo bajo o alto, sin importar el clúster.

## Dataset

- **Fuente:** UCI *Individual Household Electric Power Consumption* — DOI 10.24432/C58K54, licencia CC BY 4.0 (Hebrail y Berard). https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption
- **Tamaño:** 2.075.259 mediciones por minuto (diciembre 2006 – noviembre 2010, una vivienda), agregadas en 68.304 ventanas válidas de 30 minutos (≥ 80 % de cobertura, sin imputar).
- **Features (7):** `Global_active_power` (kW), `Global_reactive_power` (kW), `Voltage` (V), `Global_intensity` (A), `Sub_metering_1` (cocina), `Sub_metering_2` (lavandería, nevera y luces) y `Sub_metering_3` (calentador de agua y aire acondicionado), los tres últimos en Wh por minuto.
- **Referencia para Colombia:** `data/reference/consumo_electrodomesticos_colombia.xlsx` (y su CSV) contiene potencias aproximadas de electrodomésticos colombianos. Se usa **solo para facilitar el ingreso de datos y mostrar escenarios de referencia**, no para entrenar. La app convierte vatios a las variables del modelo (Wh/min = W ÷ 60; corriente = P ÷ 240 V, el voltaje del entrenamiento, para no marcar como atípicos a hogares de 120 V solo por el voltaje).
- **Limitación:** el modelo aprendió de una sola vivienda extranjera; los hábitos colombianos (cocina a gas, ducha eléctrica) difieren, por lo que los resultados son orientativos.

## Instalación local

### Requisitos
- Python 3.11, 3.12 o 3.13 y `pip`
- Conexión a internet solo para descargar el dataset si se quiere reentrenar

### Pasos

```bash
git clone https://github.com/USUARIO/energywatch-ai.git
cd energywatch-ai
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

El modelo entrenado ya viene en `models/`. Para **reentrenar** desde cero (descarga ~126 MB de UCI):

```bash
python -m src.train
```

### Ejecutar la aplicación

```bash
streamlit run app/app.py
```

Abre http://localhost:8501. Para correr las pruebas: `python -m pytest -q`.

## Uso

1. **Revisar mi consumo:** elige *Elegir mis electrodomésticos* (cantidad y minutos encendidos en los últimos 30) o *Ya conozco mis vatios*. Escribe opcionalmente un nombre y el precio de tu kWh y pulsa **Revisar mi consumo**.
2. Recibe el semáforo, el escenario de consumo (base, normal o pico), kWh y costo diario estimados y consejos.
3. **Mi historial:** gráfica y tabla de tus consultas, descarga en CSV y borrado individual o total.
4. **Demostración:** reproduce mediciones históricas reales del conjunto de evaluación (no es un medidor en vivo).
5. **Cómo funciona:** explicación técnica del modelo y métricas.

Si se ingresan valores inválidos (consumo total en 0, minutos fuera de 0–30, cantidades negativas) la app muestra un mensaje de error en lugar de fallar.

## Estructura del proyecto

```
app/app.py                    Interfaz Streamlit (5 pestañas)
src/ui.py                     Estilos, tarjeta de resultado y gráficos
src/seed_demo.py              Historial de ejemplo con ventanas reales (python -m src.seed_demo)
src/preprocessing.py          Descarga, ventanas de 30 min y transformación
src/train.py                  Búsqueda de hiperparámetros, evaluación y serialización
src/predict.py                Asignación de nuevas mediciones a núcleos DBSCAN
src/simple_input.py           Conversión vatios → variables del modelo
src/catalog.py                Catálogo de electrodomésticos de Colombia y escenarios
src/advice.py                 Semáforo, mensajes y consejos en lenguaje simple
src/database.py               Historial en SQLite (data/energywatch.db)
notebooks/01_training.ipynb   Exploración, EDA, entrenamiento y evaluación (ejecutado)
models/                       modelo.joblib y metadata.json
data/raw, data/processed      Datos originales (no versionados) y replay de prueba
data/reference/               Excel y CSV de electrodomésticos de Colombia
tests/                        Pruebas con pytest (modelo, base de datos, catálogo, interfaz)
docs/                         Arquitectura, guía de entrega, capturas y presentacion.pdf
```

## Despliegue

Streamlit Community Cloud conectado a este repositorio (rama `main`, archivo principal `app/app.py`, Python 3.12). Los artefactos del modelo pesan ~200 KB y se versionan; el dataset crudo (126 MB) no. El historial SQLite se guarda en el servidor y puede reiniciarse cuando la app se reinicia. Nunca cargues archivos Joblib de fuentes no confiables: la deserialización puede ejecutar código.

## Reproducibilidad

Semillas fijas (42 y 43), corte cronológico definido, dependencias con versión exacta en `requirements.txt` (el modelo serializado exige la misma versión de scikit-learn con la que se entrenó) y métricas guardadas en JSON.

## Autores

- _Ian Steven Cardona Gaviria_
- _Camila Peñeula_
- _Sebastian Gil_

## Licencia

Código bajo licencia MIT (ver `LICENSE`). Los datos conservan su licencia CC BY 4.0 y deben atribuirse a UCI. Documentación de DBSCAN: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
