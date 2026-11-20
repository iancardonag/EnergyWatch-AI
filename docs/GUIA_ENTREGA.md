# Guía de entrega — Actividad 3 (de local a la nube)

Estado actual: modelo entrenado, notebook ejecutado, app local funcionando, 13 pruebas pasando. **Falta lo que solo ustedes pueden hacer:** GitHub, nube, capturas, presentación y datos de autores.

## 1. Crear el repositorio y subir el proyecto (Entrega 1: 2 pts + Entrega 2: 6 pts)

1. Cada integrante crea cuenta en GitHub. **Uno** crea el repositorio `energywatch-ai` como **Public** (privado = −10 puntos) con licencia MIT y sin README (ya existe).
2. Agrega a los otros dos como *Collaborators* (Settings → Collaborators).
3. En la carpeta del proyecto:
   ```bash
   git init -b main
   git config user.name "Tu Nombre"        # cada integrante usa SU nombre y correo
   git config user.email "tu@correo.com"
   git remote add origin https://github.com/USUARIO/energywatch-ai.git
   ```
4. **Antes del primer `git add`**, confirma que no subes el dataset (126 MB): `git status` no debe listar `data/raw/household_power_consumption.txt` ni la carpeta `.venv/` (ya están en `.gitignore`).
5. Primer commit y push:
   ```bash
   git add .
   git commit -m "Estructura inicial del proyecto, modelo DBSCAN y notebook"
   git push -u origin main
   ```

## 2. Los 10 commits y que los tres tengan commits

La rúbrica exige **≥ 10 commits significativos y que todos los integrantes tengan**. Deben ser reales: repártanse trabajo que de verdad falta y que cada uno lo haga desde su computador y cuenta (`git pull` antes de empezar, `git push` al terminar). Ideas de tareas con commit propio:

| Quién | Tarea real pendiente | Ejemplo de mensaje |
|---|---|---|
| Integrante A | Completar datos de autores y README (URL, nombres) | `Completa autores y enlace de despliegue en README` |
| Integrante A | Subir capturas de la app a `docs/capturas/` | `Agrega capturas de pruebas locales` |
| Integrante B | Revisar textos y consejos de `src/advice.py` | `Ajusta consejos de ahorro a hogares colombianos` |
| Integrante B | Agregar un caso de prueba nuevo en `tests/` | `Agrega prueba de consumo bajo en advice` |
| Integrante C | Configurar y probar el despliegue | `Fija versiones de dependencias para despliegue` |
| Integrante C | Subir la presentación a `docs/presentacion.pdf` | `Agrega presentación final en PDF` |

Verifiquen el reparto con: `git shortlog -sn`. No creen commits vacíos ni de relleno: el profesor revisa el contenido ("Plagio / contribuciones" en las políticas).

## 3. Capturas de pantalla para la asesoría (Entrega 1)

Con `streamlit run app/app.py` toma y guarda en `docs/capturas/`: (1) Inicio, (2) elegir electrodomésticos con resultado 🟢, (3) resultado 🔴 de consumo alto (ej. ducha + horno + secadora), (4) modo "Ya conozco mis vatios" con un ejemplo real, (5) Mi historial con varias consultas, (6) pestaña Cómo funciona con las métricas, (7) un error controlado (consumo 0).

## 4. Desplegar en Streamlit Community Cloud (Entrega 2: 6 pts)

1. Entra a https://share.streamlit.io con la cuenta de GitHub y pulsa **Create app**.
2. Repositorio `USUARIO/energywatch-ai`, rama `main`, archivo principal `app/app.py`.
3. **Advanced settings → Python version: 3.12** (el local es 3.14; si falla la instalación con las versiones fijadas de `requirements.txt`, prueba 3.13 o pide ayuda).
4. Deploy. Prueba la URL en computador **y celular**, con un cronómetro (debe cargar en < 10 s).
5. Pega la URL en `README.md` (sección Demostración) y en los archivos `.txt` de entrega.

Cuidados:
- La app "duerme" tras días sin visitas. **Ábrela el día antes y 10 minutos antes de exponer.**
- El historial SQLite vive en el servidor y se borra si la app se reinicia; para la demo, hagan 2-3 consultas en vivo.
- El archivo `models/modelo.joblib` exige la **misma versión de scikit-learn** (1.9.1) con la que se entrenó; por eso `requirements.txt` tiene versiones exactas. No las cambien sin reentrenar.

## 5. Archivos de texto para Blackboard

- **Asesoría:** `Grupo#_Actividad3_ASESORIA.txt`. Base lista en `docs/ASESORIA_PLANTILLA.txt` (métricas reales ya incluidas; completa número de grupo, URL y fecha). Sin entrega tardía.
- **Final:** `Grupo#_Actividad3_FINAL.txt` con URL del repo, URL de la app, "no requiere credenciales" e instrucciones especiales.
- **Presentación:** `Grupo#_Presentacion_FINAL.pdf`, máximo 15 diapositivas, subir antes de las 23:59 del día anterior.

## 6. Presentación (15 diapositivas máx.)

1 Portada (nombre, DBSCAN, integrantes, URL app, URL repo) · 2-3 Problema y datos (UCI, 2.075.259 registros, 7 variables, ejemplos) · 4-5 Algoritmo y entrenamiento (por qué DBSCAN, malla de parámetros, Silhouette 0,573/0,618, ruido 5,1 %/2,9 %) · 6-8 La app (capturas, flujo, arquitectura de `docs/arquitectura.md`, stack) · 9-11 Despliegue y GitHub (Streamlit Cloud, estructura, `.gitignore`, requirements, README) · 12 Demo en vivo · 13 Desafíos (voltaje 120 V vs 240 V, DBSCAN sin `predict()`, datos de otra región) · 14 Trabajo futuro · 15 Referencias en formato IEEE.

Tiempos (12 min): problema/datos 2 · algoritmo 2 · app 2 · despliegue 3 · demo 4 · desafíos 2. Los tres deben hablar y poder explicar el código. **Plan B:** graben un video de la demo.

## 7. Checklist final contra la rúbrica

- [x] Modelo entrenado, Silhouette 0,618 en prueba (> 0,4) y serializado en `models/modelo.joblib`
- [x] Notebook ejecutado con EDA, entrenamiento y evaluación
- [x] App con ≥ 3 inputs, resultado claro y manejo de errores
- [x] `requirements.txt` con versiones exactas, `.gitignore`, `LICENSE` MIT, README > 500 palabras
- [x] Pruebas automáticas (pytest) y código formateado (PEP8/black)
- [ ] Repositorio público en GitHub con ≥ 10 commits de los 3 integrantes
- [ ] Nombres de autores y URL en el README
- [ ] Capturas de pruebas locales en `docs/capturas/`
- [ ] App desplegada con URL pública (< 10 s, también en móvil)
- [ ] Presentación PDF ≤ 15 diapositivas en `docs/presentacion.pdf`
- [ ] Video de respaldo de la demo
- [ ] Ensayo de la exposición (12 min, los tres participan)
