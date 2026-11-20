# Ejecución en Windows PowerShell / CMD

1. Descomprimir la carpeta y entrar a `energywatch-ai`.
2. Instalar Python 3.11 o 3.12. Verificar `py -3.11 --version`.
3. Crear entorno: `py -3.11 -m venv .venv`.
4. Activar desde CMD: `.venv\Scripts\activate.bat` (desde PowerShell: `.\.venv\Scripts\Activate.ps1`, si la política lo permite).
5. Ejecutar `python -m pip install -r requirements.txt`.
6. Ejecutar `python -m src.train` (descarga dataset UCI si hay acceso). Si no descarga, colocar `household_power_consumption.txt` en `data\raw\` y ejecutar otra vez.
7. Comprobar resultados en `models\metadata.json` y confirmar que `models\modelo.joblib` exista. Si hay error por no encontrar 2 clústeres válidos, consultar `models\search_results.json`: NO presentar una métrica inventada.
8. Ejecutar `python -m pytest -q`.
9. Iniciar `streamlit run app/app.py`. Abrir el enlace local mostrado por la consola, habitualmente http://localhost:8501 .
10. Entrar a **Analizar medición**, cargar un ejemplo real del conjunto de evaluación y pulsar Analizar. Repetir con un ejemplo de ruido, si existe. Usar Reproducción histórica para demostrar mediciones reales del dataset.
11. Ejecutar el notebook desde la raíz con `jupyter notebook notebooks/01_training.ipynb` (Jupyter no está incluido en requirements.txt de producción; instalar `pip install notebook` si se necesita) y guardar salidas para la entrega académica.
12. Crear repo público con commits reales por cada integrante, subir código, notebook ejecutado y artefactos entrenados si son pequeños, publicar en Streamlit y verificar URL accesible.

**Nota:** el modelo ya viene entrenado en `models/`; el paso 6 solo es necesario para reentrenar. El entrenamiento usa el archivo oficial de UCI, no datos simulados. La pestaña de la app ahora se llama **Revisar mi consumo** (en el paso 10). Para el despliegue y la entrega, ver `docs/GUIA_ENTREGA.md`.
