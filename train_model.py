import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from statsbombpy import sb
from etl import extraer_pases_y_features

print("🧠 [FASE 1] INICIANDO ENTRENAMIENTO DE LA IA (80% DE LA LIGA)")
partidos = sb.matches(competition_id=11, season_id=90)

# BARRERA DE CONTENCIÓN: Solo usamos hasta la Jornada 28
partidos_train = partidos[partidos['match_week'] <= 28].sort_values('match_week')
print(f"📚 Descargando {len(partidos_train)} partidos del pasado para estudiar...")

lista_df = []
for index, partido in partidos_train.iterrows():
    try:
        print(f"   Entrenando con: J{partido['match_week']} - {partido['home_team']} vs {partido['away_team']}")
        df = extraer_pases_y_features(partido['match_id'])
        lista_df.append(df)
    except:
        pass

# Juntamos todos los pases de las 28 jornadas (Miles de pases)
df_train_full = pd.concat(lista_df, ignore_index=True)

columnas_espaciales = ['start_x', 'start_y', 'end_x', 'end_y', 'dist_goal_start', 'dist_goal_end', 'distance_progress']
df_limpio = df_train_full.dropna(subset=columnas_espaciales + ['target']).copy()

X = df_limpio[columnas_espaciales]
y = df_limpio['target']

print(f"🌲 Construyendo el Random Forest con {len(X)} pases...")
modelo_rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
modelo_rf.fit(X, y)

modelo_lr = LogisticRegression()
modelo_lr.fit(X, y)

print("✅ Entrenamiento completado. La IA está lista para salir al mundo real.\n")