import warnings
warnings.filterwarnings('ignore')
from statsbombpy import sb
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from etl import extraer_pases_y_features

# Al importar esto, Python ejecutará la Fase 1 (Entrenamiento) automáticamente
from train_model import modelo_rf, modelo_lr, columnas_espaciales

# CONEXIÓN BBDD
CONTRASENA = "tu_contraseña" # PON TU CONTRASEÑA REAL AQUÍ
engine = create_engine(f'postgresql://postgres:{quote_plus(CONTRASENA)}@localhost:5432/laliga_xt')

print("🚀 [FASE 2] INICIANDO INFERENCIA EN PRODUCCIÓN (20% DE PRUEBA)")
partidos = sb.matches(competition_id=11, season_id=90)

# BARRERA DE CONTENCIÓN: Solo analizamos de la Jornada 29 al final (Cero fuga de datos)
partidos_test = partidos[partidos['match_week'] > 28].sort_values('match_week')
print(f"🏟️ Evaluando el peligro en {len(partidos_test)} partidos nuevos...")

es_primer_partido = True

for index, partido in partidos_test.iterrows():
    try:
        nombre_enfrentamiento = f"{partido['home_team']} vs {partido['away_team']}"
        jornada = partido['match_week']
        print(f"   Inyectando en Dashboard: J{jornada} - {nombre_enfrentamiento}...")
        
        df_nuevo = extraer_pases_y_features(partido['match_id'])
        df_limpio = df_nuevo.dropna(subset=columnas_espaciales + ['target']).copy()
        
        # La IA evalúa datos que NUNCA ha visto
        df_limpio['xT_LogReg'] = modelo_lr.predict_proba(df_limpio[columnas_espaciales])[:, 1].round(4)
        df_limpio['xT_RandForest'] = modelo_rf.predict_proba(df_limpio[columnas_espaciales])[:, 1].round(4)
        
        df_limpio['jornada'] = jornada
        df_limpio['partido_nombre'] = nombre_enfrentamiento
        
        modo = 'replace' if es_primer_partido else 'append'
        df_limpio.to_sql('pases_valorados', engine, if_exists=modo, index=False)
        es_primer_partido = False
        
    except Exception as e:
        print(f"❌ Error en el partido: {e}")

print("\n✅ ¡Misión cumplida! Base de datos reiniciada y actualizada con el 20% puro.")