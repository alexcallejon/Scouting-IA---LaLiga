import pandas as pd
import numpy as np
from statsbombpy import sb
import warnings

warnings.filterwarnings('ignore')

def extraer_pases_y_features(match_id):
    """
    Pipeline ETL para extraer pases, calcular métricas espaciales
    y asignar la variable Target (1 = pase de jugada que acaba en tiro).
    """
    print(f"📡 Descargando datos del partido ID: {match_id}...")
    
    # 1. EXTRACT: Descargar todos los eventos del partido
    eventos = sb.events(match_id=match_id)
    
    # --- NUEVA LÓGICA DE LA SEMANA 2 (EL TARGET) ---
    # Rastrear los tiros
    tiros = eventos[eventos['type'] == 'Shot']
    # Anotar los IDs de posesión únicos que terminaron en tiro
    posesiones_peligrosas = tiros['possession'].unique()
    # -----------------------------------------------
    
    # 2. TRANSFORM: Quedarnos solo con los pases válidos
    pases = eventos[eventos['type'] == 'Pass'].copy()
    pases = pases.dropna(subset=['location', 'pass_end_location'])
    
    # Etiquetar los pases comprobando si su 'possession' está en la lista de peligrosas
    pases['target'] = pases['possession'].isin(posesiones_peligrosas).astype(int)
    
    # 3. TRANSFORM (1NF): Separar coordenadas
    pases[['start_x', 'start_y']] = pd.DataFrame(pases['location'].tolist(), index=pases.index)
    pases[['end_x', 'end_y']] = pd.DataFrame(pases['pass_end_location'].tolist(), index=pases.index)
    
    # 4. FEATURE ENGINEERING (Geometría del campo)
    GOAL_X = 120
    GOAL_Y = 40
    pases['dist_goal_start'] = np.sqrt((GOAL_X - pases['start_x'])**2 + (GOAL_Y - pases['start_y'])**2)
    pases['dist_goal_end'] = np.sqrt((GOAL_X - pases['end_x'])**2 + (GOAL_Y - pases['end_y'])**2)
    pases['distance_progress'] = pases['dist_goal_start'] - pases['dist_goal_end']
    
    # 5. LIMPIEZA FINAL: Seleccionar columnas útiles (añadimos 'possession' y 'target')
    columnas_finales = [
        'match_id', 'id', 'possession', 'minute', 'second', 'team', 'player', 
        'start_x', 'start_y', 'end_x', 'end_y', 
        'dist_goal_start', 'dist_goal_end', 'distance_progress',
        'pass_outcome', 'target' 
    ]
    
    return pases[columnas_finales]


# --- EJECUCIÓN ---
if __name__ == "__main__":
    partidos_laliga = sb.matches(competition_id=11, season_id=90)
    partido_prueba_id = partidos_laliga.iloc[0]['match_id']
    equipo_local = partidos_laliga.iloc[0]['home_team']
    equipo_visitante = partidos_laliga.iloc[0]['away_team']
    
    print(f"🏟️ Partido seleccionado: {equipo_local} vs {equipo_visitante}")
    
    df_pases = extraer_pases_y_features(partido_prueba_id)
    
    # Comprobación de calidad del dato
    print("\n✅ ETL y Target calculados correctamente.")
    print("Resumen de pases del partido:")
    print(df_pases['target'].value_counts().rename(index={0: 'Pases sin peligro (0)', 1: 'Pases que acabaron en tiro (1)'}))