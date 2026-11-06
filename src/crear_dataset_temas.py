import pandas as pd
import numpy as np

print("1. Extrayendo temas del archivo original...")
cols_temas = ['rcid', 'me', 'nu', 'di', 'hr', 'co', 'ec']
df_temas = pd.read_csv("raw/asamblea.csv", encoding='latin-1', usecols=cols_temas, low_memory=False)

# Limpiar y asegurar que sean números enteros (0 o 1)
df_temas = df_temas.fillna(0)
df_temas[cols_temas[1:]] = df_temas[cols_temas[1:]].astype(int)
# Eliminar duplicados a nivel de resolución
df_temas = df_temas.drop_duplicates(subset=['rcid'])

# Nuevo diccionario de temas (Desarme y Nucleares unidos, y Otros Temas)
temas_dict = {
    'Todas las Resoluciones': None,
    'Derechos Humanos': ['hr'],
    'Medio Oriente': ['me'],
    'Desarme y Armas Nucleares': ['di', 'nu'],
    'Colonialismo y Soberanía': ['co'],
    'Desarrollo Económico': ['ec'],
    'Otros Temas': ['otros']
}

print("2. Cargando datos limpios de votaciones...")
df = pd.read_csv("data/processed/ag_clean.csv")
df = df.dropna(subset=['vote_num'])

# Unir votaciones con los temas
df = pd.merge(df, df_temas, on='rcid', how='left')
df[cols_temas[1:]] = df[cols_temas[1:]].fillna(0)

alias = {
    'Iran': 'Iran (Islamic Republic of)', 'South Korea': 'Republic of Korea',
    'North Korea': 'Democratic People\'s Republic of Korea', 'Vietnam': 'Viet Nam',
    'Bolivia': 'Bolivia (Plurinational State of)', 'Venezuela': 'Venezuela (Bolivarian Republic of)',
    'Russia': 'Russian Federation', 'United States': 'United States of America',
    'UK': 'United Kingdom', 'Syria': 'Syrian Arab Republic',
    'Tanzania': 'United Republic of Tanzania', 'Moldova': 'Republic of Moldova'
}
df['Countryname'] = df['Countryname'].replace(alias)

regiones = {
    'Norteamérica': ['United States of America', 'Canada', 'Mexico'],
    'Europa Occidental': ['United Kingdom', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 'Belgium', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Switzerland', 'Austria', 'Ireland', 'Portugal', 'Greece', 'Australia', 'New Zealand', 'Japan', 'Republic of Korea'],
    'América Latina': ['Brazil', 'Argentina', 'Cuba', 'Venezuela (Bolivarian Republic of)', 'Chile', 'Colombia', 'Peru', 'Bolivia (Plurinational State of)', 'Ecuador', 'Uruguay', 'Paraguay', 'Guatemala', 'Honduras', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama', 'Dominican Republic'],
    'Europa del Este': ['Russian Federation', 'Ukraine', 'Poland', 'Belarus', 'Georgia', 'Kazakhstan', 'Uzbekistan', 'Romania', 'Bulgaria', 'Czech Republic', 'Hungary', 'Slovakia', 'Serbia', 'Armenia', 'Azerbaijan'],
    'MENA': ['Saudi Arabia', 'Iran (Islamic Republic of)', 'Egypt', 'Algeria', 'Morocco', 'Iraq', 'Israel', 'Turkey', 'Syrian Arab Republic', 'Jordan', 'United Arab Emirates', 'Lebanon', 'Kuwait', 'Qatar', 'Tunisia'],
    'África Subsahariana': ['South Africa', 'Nigeria', 'Kenya', 'Ethiopia', 'Ghana', 'Senegal', 'Angola', 'Mozambique', 'United Republic of Tanzania', 'Zimbabwe', 'Cameroon', 'Ivory Coast', 'Uganda', 'Zambia'],
    'Asia Oriental': ['China', 'Indonesia', 'Viet Nam', 'Thailand', 'Malaysia', 'Philippines', 'Singapore', 'Cambodia', 'Laos', 'Mongolia'],
    'Asia Meridional': ['India', 'Pakistan', 'Bangladesh', 'Sri Lanka', 'Nepal', 'Afghanistan', 'Maldives', 'Bhutan']
}

referentes = {
    'EE.UU.': 'United States of America', 'Francia': 'France', 'Brasil': 'Brazil',
    'Rusia': 'Russian Federation', 'Arabia Saudita': 'Saudi Arabia', 'Sudáfrica': 'South Africa', 'China': 'China'
}

resultados = []

print("3. Calculando afinidades por tema...")
for tema_nombre, tema_cols in temas_dict.items():
    print(f"   - Procesando tema: {tema_nombre}")
    
    df_tema = df.copy()
    
    # Lógica de filtrado de temas
    if tema_cols is None:
        pass # Todas las resoluciones (sin filtro)
    elif tema_cols == ['otros']:
        # Otros temas: donde me, nu, di, hr, co, ec sean TODOS 0
        df_tema = df_tema[(df_tema['me'] == 0) & (df_tema['nu'] == 0) & 
                          (df_tema['di'] == 0) & (df_tema['hr'] == 0) & 
                          (df_tema['co'] == 0) & (df_tema['ec'] == 0)]
    else:
        # Si es una lista (ej. ['di', 'nu']), incluir si al menos una es 1
        df_tema = df_tema[df_tema[tema_cols].sum(axis=1) > 0]
        
    if df_tema.empty: continue

    for ref_nombre, ref_pais in referentes.items():
        df_ref = df_tema[df_tema['Countryname'] == ref_pais][['rcid', 'year', 'vote_num']]
        df_ref = df_ref.rename(columns={'vote_num': 'vote_ref'})
        
        merged = pd.merge(df_tema, df_ref, on='rcid', suffixes=('', '_y'))
        # Coincidencia: 1 si es igual, 0 si es distinto (Abstención 0 == 0 cuenta como 1)
        merged['coincide'] = (merged['vote_num'] == merged['vote_ref']).astype(int)
        
        agrupado = merged.groupby(['Countryname', 'year'])['coincide'].mean().reset_index()
        agrupado['afinidad'] = agrupado['coincide'] * 100
        agrupado['referente'] = ref_nombre
        agrupado['tema'] = tema_nombre
        
        def get_region(pais):
            for reg, paises in regiones.items():
                if pais in paises: return reg
            return 'Otros'
            
        agrupado['region'] = agrupado['Countryname'].apply(get_region)
        agrupado = agrupado[agrupado['region'] != 'Otros']
        resultados.append(agrupado[['tema', 'referente', 'region', 'Countryname', 'year', 'afinidad']])

df_final = pd.concat(resultados, ignore_index=True)

print("4. Calculando promedios regionales...")
df_regiones = df_final.groupby(['tema', 'referente', 'region', 'year'])['afinidad'].mean().reset_index()

# Excluir al referente de su propia región
for tema_nombre in temas_dict.keys():
    for ref_nombre, ref_pais in referentes.items():
        for reg_nombre, paises_region in regiones.items():
            if ref_pais in paises_region:
                df_temp = df_final[(df_final['tema'] == tema_nombre) & 
                                   (df_final['referente'] == ref_nombre) & 
                                   (df_final['region'] == reg_nombre) & 
                                   (df_final['Countryname'] != ref_pais)]
                if not df_temp.empty:
                    nuevo_prom = df_temp.groupby(['tema', 'referente', 'region', 'year'])['afinidad'].mean().reset_index()
                    # Eliminar el promedio viejo y agregar el nuevo
                    df_regiones = df_regiones[~((df_regiones['tema'] == tema_nombre) & 
                                                (df_regiones['referente'] == ref_nombre) & 
                                                (df_regiones['region'] == reg_nombre))]
                    df_regiones = pd.concat([df_regiones, nuevo_prom], ignore_index=True)

df_final.to_csv("data/processed/dataset_paises_temas.csv", index=False)
df_regiones.to_csv("data/processed/dataset_regiones_temas.csv", index=False)

print("\n¡Datasets con temas generados con éxito!")
print(f"Total de registros país-año-tema-referente: {len(df_final)}")
