import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from mplsoccer import Pitch
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import io

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Scouting IA - LaLiga", layout="wide", page_icon="⚽")

# 2. CARGA DE DATOS
@st.cache_data
def cargar_datos():
    USUARIO = "postgres"
    CONTRASENA = "alex5753"  # PON TU CONTRASEÑA REAL AQUÍ
    HOST = "localhost"
    PUERTO = "5432"
    BBDD = "laliga_xt"
    
    engine = create_engine(f'postgresql://{USUARIO}:{quote_plus(CONTRASENA)}@{HOST}:{PUERTO}/{BBDD}')
    df = pd.read_sql('SELECT * FROM pases_valorados', engine)
    
    def limpiar_nombre(nombre):
        nombre = str(nombre)
        excepciones = {
            "Lionel Andrés Messi Cuccittini": "L. Messi",
            "Sergio Busquets i Burgos": "S. Busquets",
            "Jordi Alba Ramos": "J. Alba",
            "Sergi Roberto Carnicer": "S. Roberto",
            "Anssumane Fati": "A. Fati"
        }
        if nombre in excepciones:
            return excepciones[nombre]
        
        partes = nombre.split()
        if len(partes) == 1:
            return partes[0]
        return f"{partes[0][0]}. {partes[1]}"

    df['player_clean'] = df['player'].apply(limpiar_nombre)
    return df

df_pases = cargar_datos()

# 3. BARRA LATERAL (NUEVA LÓGICA LOGÍSTICA: PARTIDO -> EQUIPO)
st.sidebar.title("⚙️ Panel de Scouting")
st.sidebar.markdown("Filtros de Análisis:")

# Comprobamos si la base de datos tiene la estructura nueva de jornadas
if 'partido_nombre' in df_pases.columns and 'jornada' in df_pases.columns:
    
    # 1º FILTRO: Elegir el Contexto (Partido específico o Global)
    partidos_unicos = df_pases[['jornada', 'partido_nombre']].drop_duplicates().sort_values('jornada')
    lista_opciones_partido = ["Análisis Global (Toda la temporada)"] + [f"Jornada {row['jornada']}: {row['partido_nombre']}" for _, row in partidos_unicos.iterrows()]
    
    partido_seleccionado = st.sidebar.selectbox("1. Contexto de Partido", lista_opciones_partido)
    
    # Filtramos la base de datos temporalmente para quedarnos SOLO con los datos de ese partido
    if partido_seleccionado == "Análisis Global (Toda la temporada)":
        df_temp = df_pases
    else:
        nombre_real_partido = partido_seleccionado.split(": ")[1]
        df_temp = df_pases[df_pases['partido_nombre'] == nombre_real_partido]
        
else:
    # Por si acaso la base de datos no está actualizada aún
    df_temp = df_pases
    st.sidebar.warning("Aún no hay datos de jornadas. Mostrando modo global.")

# 2º FILTRO: Elegir el Equipo (La lista de equipos ahora se limita a lo que haya en df_temp)
# Si elegiste un partido, aquí solo aparecerán los 2 equipos que lo jugaron.
equipos_disponibles = sorted(df_temp['team'].dropna().unique().tolist())
equipo_seleccionado = st.sidebar.selectbox("2. Equipo a analizar", equipos_disponibles)

# Filtro final que usa el resto de la web para dibujar gráficos y KPIs
df_analisis = df_temp[df_temp['team'] == equipo_seleccionado]


# 4. PESTAÑAS (TABS)
tab1, tab2 = st.tabs(["📊 Informe de Rendimiento", "🏟️ Pizarra Táctica"])

with tab1:
    st.header(f"Peligro Esperado (xT) - {equipo_seleccionado}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Pases Analizados", len(df_analisis))
    col2.metric("Pases Críticos (xT > 50%)", len(df_analisis[df_analisis['xT_RandForest'] > 0.5]))
    
    if not df_analisis.empty:
        mvp = df_analisis.groupby('player_clean')['xT_RandForest'].max().idxmax()
        col3.metric("MVP del Equipo", mvp)
        
        st.markdown("---")
        top_jugadores = df_analisis.groupby('player_clean')['xT_RandForest'].max().sort_values(ascending=False).head(10).reset_index()
        fig_barras = px.bar(
            top_jugadores, x='xT_RandForest', y='player_clean', orientation='h',
            color='xT_RandForest', color_continuous_scale='viridis',
            labels={'xT_RandForest': 'Probabilidad de Tiro (xT)', 'player_clean': 'Jugador'}
        )
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_barras, use_container_width=True)

with tab2:
    st.header("Mapa de Pases Letales")
    num_pases = st.slider("¿Cuántos pases letales dibujar?", 1, 10, 3)
    
    if not df_analisis.empty:
        top_pases_pitch = df_analisis.sort_values(by='xT_RandForest', ascending=False).head(num_pases)
        
        fig, ax = plt.subplots(figsize=(16, 10))
        fig.patch.set_facecolor('#141414')
        pitch = Pitch(pitch_type='statsbomb', pitch_color='#1e1e1e', line_color='#4a4a4a', linewidth=1.5, goal_type='box')
        pitch.draw(ax=ax)
        
        pitch.scatter(top_pases_pitch.start_x, top_pases_pitch.start_y, s=200, 
                      color='#141414', edgecolors='#00ffcc', linewidth=2, zorder=3, ax=ax)
        
        pitch.lines(top_pases_pitch.start_x, top_pases_pitch.start_y, 
                    top_pases_pitch.end_x, top_pases_pitch.end_y,
                    comet=True, transparent=True, color='#00ffcc', linewidth=5, zorder=2, ax=ax)
        
        efecto_texto = [path_effects.withStroke(linewidth=3, foreground='#141414')]
        
        for i, row in top_pases_pitch.iterrows():
            texto = f"{row['player_clean']} ({row['xT_RandForest']:.2f})"
            ax.text(row['start_x'], row['start_y'] - 3, texto, 
                    color='white', fontsize=10, fontweight='bold', ha='center',
                    path_effects=efecto_texto)
        
        buf = io.BytesIO()
        fig.savefig(buf, format="png", transparent=True, dpi=300)
        st.image(buf, use_container_width=True)