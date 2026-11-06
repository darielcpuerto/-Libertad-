import pandas as pd
import warnings
warnings.filterwarnings('ignore')

path_raw = "raw/"
path_proc = "data/processed/"

print("1. Procesando Asamblea General (esto puede tardar un poco)...")
df_ag = pd.read_csv(path_raw + "asamblea.csv", encoding='latin-1', low_memory=False)
df_ag = df_ag[df_ag['year'] >= 1992]
df_ag = df_ag[df_ag['vote'] != 9] # Eliminar 'No miembro'
map_votos = {1: 'Sí', 2: 'Abstención', 3: 'No', 8: 'Ausente'}
df_ag['vote_text'] = df_ag['vote'].map(map_votos)
df_ag.to_csv(path_proc + "ag_votes.csv", index=False)

print("2. Procesando Votos del Consejo de Seguridad...")
df_sc = pd.read_csv(path_raw + "sc_votos.csv")
df_sc['date'] = pd.to_datetime(df_sc['date'])
df_sc = df_sc[df_sc['date'].dt.year >= 1992]
df_sc.to_csv(path_proc + "sc_votes.csv", index=False)

print("3. Procesando Vetos del Consejo de Seguridad...")
df_vetos = pd.read_csv(path_raw + "sc_vetos.csv")
df_vetos = df_vetos[df_vetos['year'] >= 1992]
cols_pms = ['china', 'russian_federation_ussr', 'france', 'united_states', 'united_kingdom']
df_vetos_melt = df_vetos.melt(id_vars=['year', 'date', 'short_agenda'], 
                              value_vars=cols_pms, 
                              var_name='Pais', 
                              value_name='Veto')
df_vetos_melt = df_vetos_melt[df_vetos_melt['Veto'] == 1]
df_vetos_melt['Pais'] = df_vetos_melt['Pais'].replace('russian_federation_ussr', 'Rusia/URSS')
df_vetos_melt.to_csv(path_proc + "sc_vetos.csv", index=False)

print("4. Procesando Miembros del Consejo de Seguridad...")
df_miembros = pd.read_csv(path_raw + "sc_miembros.csv")
df_miembros = df_miembros[df_miembros['year'] >= 1992]
df_miembros.to_csv(path_proc + "sc_miembros.csv", index=False)

print("¡Limpieza terminada! Archivos guardados en data/processed/")
