#  Scouting IA: Análisis de Peligro Esperado (xT) con Machine Learning

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red.svg)
![Machine Learning](https://img.shields.io/badge/Machine_Learning-Random_Forest-green.svg)

##  Descripción del Proyecto
Este proyecto es un **Pipeline de Datos y Dashboard Interactivo** diseñado para departamentos de Scouting y Análisis Táctico en fútbol profesional. Utiliza datos de eventos (event-data) para calcular el **Peligro Esperado (xT)** de los pases mediante algoritmos de Inteligencia Artificial.

El sistema identifica patrones geométricos de pases que, aunque no terminen en asistencia directa, rompen líneas defensivas e incrementan significativamente la probabilidad de tiro (ej. "el pase de la muerte").

## 🧠 Modelos de Machine Learning Evaluados
El cálculo del Peligro Esperado (xT) se aborda como un problema de clasificación probabilística. Para evaluar el rendimiento, el pipeline genera predicciones simultáneas con dos algoritmos:

*   **Regresión Logística (Baseline):** Utilizada como modelo base por su rapidez. Sin embargo, en el fútbol, las relaciones espaciales rara vez son lineales (ej. un pase hacia atrás puede ser letal si asiste a un jugador de cara a portería), por lo que este algoritmo presenta limitaciones geométricas.
*   **Random Forest Classifier (Modelo Principal):** Algoritmo de ensamble basado en múltiples árboles de decisión. Destaca por su capacidad para capturar relaciones no lineales y patrones espaciales complejos entre las coordenadas de inicio/fin y la distancia a portería, ofreciendo una métrica de peligro mucho más realista y ajustada al contexto táctico.

##  Arquitectura y Flujo de Datos
El proyecto simula un entorno de producción real dividiendo el proceso en 4 scripts principales:

1. **ETL (`etl.py`):** Consumo de la API de StatsBomb (Open Data), limpieza de coordenadas espaciales y cálculo de vectores de progreso (`distance_progress`).
2. **Data Science (`train_model.py`):** Entrenamiento de un modelo `RandomForestClassifier` utilizando un split temporal (Jornadas 1-28 para entrenamiento, Jornadas 29+ para producción) para evitar *Data Leakage*.
3. **Persistencia (`05_produccion.py`):** Predicción de las jornadas restantes y carga automatizada a una base de datos relacional **PostgreSQL** para consumo rápido.
4. **Data App (`app.py`):** Interfaz gráfica web construida con **Streamlit**, implementando filtros en cascada (Contexto -> Equipo) y renderizado panorámico 2D del terreno de juego.

##  Notas sobre los Datos
Los datos utilizados provienen del tier *Open Data* de StatsBomb. Para la competición evaluada (LaLiga 20/21), el proveedor incluye exclusivamente los partidos disputados por el FC Barcelona ("Messi Data Biography"). El pipeline está preparado para procesar el 100% de la liga introduciendo credenciales de pago en la API.

## Instalación y Uso

Para ejecutar este proyecto en tu máquina local, sigue estos pasos:

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/alexcallejon/scouting-ia-laliga.git](https://github.com/alexcallejon/scouting-ia-laliga.git)
   cd scouting-ia-laliga
   ```

2. **Instalar las dependencias:**
   Se recomienda crear un entorno virtual previamente. Luego, instala las librerías necesarias ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar la Base de Datos:**
   * Crea una base de datos local en PostgreSQL llamada `laliga_xt`.
   * Abre el archivo `05_produccion.py` e introduce tu contraseña local de Postgres en la variable correspondiente.

4. **Ejecutar el Pipeline de Datos:**
   Este script descargará los datos de la API, entrenará la IA con el 80% de la temporada (J1-J28) y volcará las predicciones del 20% de prueba en tu base de datos (puede tardar unos 10-15 minutos):
   ```bash
   python 05_produccion.py
   ```

5. **Lanzar el Dashboard:**
   Una vez terminada la carga en la base de datos, arranca la interfaz web interactiva:
   ```bash
   streamlit run app.py
   ```
