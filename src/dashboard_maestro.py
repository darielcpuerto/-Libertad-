import pandas as pd
import plotly.graph_objects as go
import json

print("1. Cargando datasets...")
df_regiones = pd.read_csv("data/processed/dataset_regiones_temas.csv")
df_paises = pd.read_csv("data/processed/dataset_paises_temas.csv")

renombrar_temas = {
    'Colonialismo y Soberanía': 'Soberanía y Autodeterminación',
    'Desarrollo Económico': 'Economía y Medio Ambiente',
    'Medio Oriente': 'Conflictos en el Medio Oriente'
}
df_regiones['tema'] = df_regiones['tema'].replace(renombrar_temas)
df_paises['tema'] = df_paises['tema'].replace(renombrar_temas)
df_regiones['region'] = df_regiones['region'].replace({'MENA': 'Norte de África y Medio Oriente'})
df_paises['region'] = df_paises['region'].replace({'MENA': 'Norte de África y Medio Oriente'})

referentes = ['EE.UU.', 'Rusia', 'China', 'Francia', 'Brasil', 'Sudáfrica', 'Arabia Saudita']
temas = ['Todas las Resoluciones', 'Derechos Humanos', 'Conflictos en el Medio Oriente', 'Desarme y Armas Nucleares', 'Soberanía y Autodeterminación', 'Economía y Medio Ambiente', 'Otros Temas']

colores_regiones = {
    'Norteamérica': '#2B4C7E', 
    'América Latina': '#8B1C1C', 
    'Europa Occidental': '#4A7C59',
    'Europa del Este': '#5D4B6B', 
    'Norte de África y Medio Oriente': '#C87E3F', 
    'África Subsahariana': '#6B4C3A', 
    'Asia Oriental': '#B56576', 
    'Asia Meridional': '#6B705C'
}

paises_unicos = sorted(df_paises['Countryname'].unique())

fig = go.Figure()
trace_meta = []

print("2. Construyendo trazos...")
for ref in referentes:
    for tema in temas:
        df_reg = df_regiones[(df_regiones['referente'] == ref) & (df_regiones['tema'] == tema)]
        df_pai = df_paises[(df_paises['referente'] == ref) & (df_paises['tema'] == tema)]

        for region in df_reg['region'].unique():
            df_r = df_reg[df_reg['region'] == region].sort_values('year')
            fig.add_trace(go.Scatter(
                x=df_r['year'].astype(str), y=df_r['afinidad'],
                mode='lines', name=region, showlegend=False,
                line=dict(width=3.5, color=colores_regiones.get(region, '#000')),
                visible=False,
                hovertemplate=f"<b style='color:{colores_regiones.get(region, '#000')}'>{region}</b>: %{{y:.2f}}%<extra></extra>"
            ))
            trace_meta.append({'ref': ref, 'tema': tema, 'type': 'region', 'name': region})

        for pais in df_pai['Countryname'].unique():
            df_p = df_pai[df_pai['Countryname'] == pais].sort_values('year')
            region_pais = df_p['region'].iloc[0]
            fig.add_trace(go.Scatter(
                x=df_p['year'].astype(str), y=df_p['afinidad'],
                mode='lines', name=pais, showlegend=False,
                line=dict(width=1.5, dash='dot', color=colores_regiones.get(region_pais, '#888')),
                opacity=0.8, visible=False,
                hovertemplate=f"<b style='color:{colores_regiones.get(region_pais, '#888')}'>{pais}</b>: %{{y:.2f}}%<extra></extra>"
            ))
            trace_meta.append({'ref': ref, 'tema': tema, 'type': 'pais', 'name': pais})

fig.update_layout(
    title=dict(text="Alineación Geopolítica", font=dict(size=20, family="Georgia, serif", color="#2c2c2c")),
    xaxis_title="Año", 
    yaxis_title="Votos Coincidentes (%)",
    font=dict(family="Helvetica Neue, Arial, sans-serif", color="#4a4a4a"),
    yaxis=dict(range=[-5, 105], showgrid=True, gridcolor='#e8e5df', zeroline=False), 
    height=480, 
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#ffffff", font_size=13, font_family="Helvetica, sans-serif", bordercolor="#d1ccc0"),
    xaxis=dict(
        type='category', 
        tickangle=-45,
        showgrid=False,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikethickness=1, 
        spikecolor="#a4a4a4",
        spikedash="dot"
    ),
    margin=dict(l=50, r=20, t=50, b=60), 
    showlegend=False, 
    dragmode=False,
    plot_bgcolor='#FAF8F5',
    paper_bgcolor='#FAF8F5' 
)

config = {'scrollZoom': False, 'displayModeBar': False, 'doubleClick': False}

print("3. Empaquetando HTML...")
plot_html = fig.to_html(full_html=False, include_plotlyjs=True, div_id="myPlotDiv", config=config)

opciones_ref = "".join([f'<option value="{r}">{r}</option>' for r in referentes])
opciones_tema = "".join([f'<option value="{t}">{t}</option>' for t in temas])

html_regiones = ""
for reg, color in colores_regiones.items():
    checked = "checked" if reg in ['América Latina', 'Europa Occidental'] else ""
    html_regiones += f'<label class="checkbox-label"><input type="checkbox" class="region-check" value="{reg}" {checked} onchange="limitSelection(this)"><span class="color-box" style="background:{color}"></span>{reg}</label>'

html_paises = ""
for pais in paises_unicos:
    # SELECCIÓN POR DEFECTO DE ISRAEL
    checked_pais = "checked" if pais == "Israel" else ""
    html_paises += f'<label class="checkbox-label pais-item"><input type="checkbox" class="pais-check" value="{pais}" {checked_pais} onchange="limitSelection(this)">{pais}</label>'

meta_json = json.dumps(trace_meta)

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ONU: Democracia o Compromisos</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:ital,wght@0,600;1,600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #F3F0EB;
            --surface-color: #FAF8F5;
            --text-main: #1A1A1A;
            --text-muted: #6B6B6B;
            --accent-wine: #6B1D24;
            --border-color: #E2DDD4;
        }}
        body {{ font-family: 'Inter', sans-serif; background-color: var(--bg-color); margin: 0; padding: 20px; color: var(--text-main); }}
        .container {{ max-width: 1200px; margin: auto; }}
        
        /* Header Editorial */
        .header {{ margin-bottom: 30px; border-bottom: 1px solid var(--border-color); padding-bottom: 20px; }}
        .kicker {{ font-size: 12px; text-transform: uppercase; letter-spacing: 2px; color: var(--accent-wine); font-weight: 600; margin-bottom: 10px; }}
        h1 {{ font-family: 'Playfair Display', serif; font-size: 38px; margin: 0 0 15px 0; font-weight: 600; line-height: 1.1; }}
        h1 i {{ font-style: italic; color: var(--accent-wine); }}
        
        /* Subtítulo tipo artículo periodístico */
        .subtitle {{ font-family: 'Georgia', serif; font-size: 18px; color: #4a4a4a; margin: 0 0 10px 0; font-weight: 400; line-height: 1.7; max-width: 950px; text-align: justify; }}
        .aside-note {{ font-family: 'Inter', sans-serif; font-size: 14px; color: var(--text-muted); font-style: italic; margin: 0; display: block; }}
        
        /* Controles tipo píldora */
        .controls {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
        .control-group {{ display: flex; flex-direction: column; flex: 1; min-width: 200px; }}
        label.control-label {{ font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }}
        select {{ padding: 14px 20px; border: 1px solid var(--border-color); border-radius: 30px; font-size: 15px; background: #ffffff; color: var(--text-main); font-weight: 500; cursor: pointer; outline: none; transition: all 0.2s; font-family: 'Inter', sans-serif; appearance: none; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }}
        select:focus {{ border-color: var(--accent-wine); box-shadow: 0 0 0 3px rgba(107, 29, 36, 0.1); }}
        
        /* Paneles de selección */
        .selection-panel {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
        .panel-box {{ flex: 1; min-width: 280px; background: var(--surface-color); border: 1px solid var(--border-color); border-radius: 16px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }}
        .panel-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }}
        .panel-title {{ font-family: 'Playfair Display', serif; font-weight: 600; font-size: 18px; color: var(--text-main); }}
        
        /* Contador */
        .counter {{ font-size: 12px; font-weight: 600; color: #fff; background: var(--text-main); padding: 4px 12px; border-radius: 20px; letter-spacing: 0.5px; }}
        
        /* Checkboxes y fuentes más grandes */
        .checkbox-label {{ display: flex; align-items: center; font-size: 16px; margin-bottom: 14px; cursor: pointer; color: var(--text-main); transition: color 0.2s; }}
        .checkbox-label:hover {{ color: var(--accent-wine); }}
        .checkbox-label input {{ margin-right: 12px; cursor: pointer; width: 18px; height: 18px; accent-color: var(--accent-wine); }}
        .color-box {{ width: 16px; height: 16px; border-radius: 50%; margin-right: 12px; display: inline-block; }}
        
        .paises-scroll {{ max-height: 220px; overflow-y: auto; padding-right: 10px; }}
        .paises-scroll::-webkit-scrollbar {{ width: 4px; }}
        .paises-scroll::-webkit-scrollbar-thumb {{ background: #d1ccc0; border-radius: 4px; }}
        
        #buscadorPaises {{ width: 100%; padding: 12px 16px; margin-bottom: 15px; border: 1px solid var(--border-color); border-radius: 30px; box-sizing: border-box; font-size: 15px; font-family: 'Inter', sans-serif; outline: none; background: #fff; }}
        #buscadorPaises:focus {{ border-color: var(--accent-wine); }}
        
        .btn-clear {{ background: transparent; color: var(--text-muted); border: 1px solid var(--border-color); padding: 6px 14px; border-radius: 30px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; text-transform: uppercase; letter-spacing: 0.5px; }}
        .btn-clear:hover {{ background: var(--text-main); color: #fff; border-color: var(--text-main); }}

        /* Tarjeta del gráfico e instrucciones */
        .chart-container {{ background: var(--surface-color); border: 1px solid var(--border-color); border-radius: 16px; padding: 10px 10px 0 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); overflow: hidden; }}
        .instructions {{ background: #fff; border-top: 1px solid var(--border-color); padding: 20px; border-radius: 0 0 16px 16px; font-size: 14px; line-height: 1.6; color: #4a4a4a; }}
        .instructions b {{ color: var(--accent-wine); font-size: 15px; }}
        .instructions ul {{ margin: 10px 0 0 0; padding-left: 20px; }}
        .instructions li {{ margin-bottom: 8px; }}

        @media (max-width: 768px) {{
            h1 {{ font-size: 30px; }}
            .subtitle {{ font-size: 16px; text-align: left; }}
            .controls {{ flex-direction: column; gap: 15px; }}
            .selection-panel {{ flex-direction: column; gap: 15px; }}
            .panel-box {{ min-width: 100%; padding: 15px; }}
            .checkbox-label {{ font-size: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="kicker">Análisis de Votaciones · ONU · A partir de 1992</div>
            <h1>La ONU: <i>Democracia o Compromisos</i></h1>
            <p class="subtitle">La ONU promete ser un espacio igualitario para el debate y la toma de decisiones relevantes en la agenda internacional, pero al mirar más de cerca el comportamiento de los países miembros se aprecia una determinada afinidad con ciertos referentes regionales, incluso si estos se encuentran en el otro hemisferio. <b>Explora las relaciones de poder que mueven el mundo en la actualidad y descubre las afinidades de cada país.</b></p>
            <span class="aside-note">* En el ejemplo se observa cómo la afinidad de Israel y Europa Occidental es mayor que la de América Latina con su vecino Estados Unidos, ¿curioso no?</span>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label class="control-label">Potencia Referente</label>
                <select id="refSelect" onchange="updateChart()">
                    {opciones_ref}
                </select>
            </div>
            <div class="control-group">
                <label class="control-label">Eje Temático</label>
                <select id="temaSelect" onchange="updateChart()">
                    {opciones_tema}
                </select>
            </div>
        </div>

        <div class="selection-panel">
            <div class="panel-box">
                <div class="panel-header">
                    <div class="panel-title">Promedios Regionales</div>
                </div>
                {html_regiones}
            </div>
            
            <div class="panel-box">
                <div class="panel-header">
                    <div class="panel-title">Mostrando</div>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span class="counter" id="contadorSeleccion">3/8</span>
                        <button class="btn-clear" onclick="clearAll()">Limpiar</button>
                    </div>
                </div>
                <input type="text" id="buscadorPaises" onkeyup="filtrarPaises()" placeholder="Buscar país...">
                <div class="paises-scroll" id="listaPaises">
                    {html_paises}
                </div>
            </div>
        </div>

        <div class="chart-container">
            {plot_html}
            <div class="instructions">
                <b>💡 ¿Cómo leer e interactuar con este gráfico?</b>
                <ul>
                    <li>Toca cualquier parte de las líneas para ver los datos de ese año. Verás un cuadro con los porcentajes correspondientes.</li>
                    <li>Usa los menús de arriba para cambiar la potencia (EE.UU., China, etc.) o el tema que se está votando (Derechos Humanos, Economía, etc.).</li>
                    <li>Marca o desmarca las regiones y los países de las listas para comparar sus comportamientos. Puedes mostrar hasta 8 líneas a la vez.</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        var traceMeta = {meta_json};
        
        function updateCounter() {{
            var totalChecked = document.querySelectorAll('.region-check:checked').length + 
                               document.querySelectorAll('.pais-check:checked').length;
            var counterEl = document.getElementById('contadorSeleccion');
            counterEl.innerText = totalChecked + "/8";
            if(totalChecked === 8) {{
                counterEl.style.background = "#8B1C1C";
            }} else {{
                counterEl.style.background = "#1A1A1A";
            }}
        }}

        function limitSelection(checkbox) {{
            var totalChecked = document.querySelectorAll('.region-check:checked').length + 
                               document.querySelectorAll('.pais-check:checked').length;
            if (totalChecked > 8) {{
                checkbox.checked = false;
                alert("Para que los datos se lean bien, puedes mostrar un máximo de 8 líneas a la vez.");
            }} else {{
                updateChart();
                updateCounter();
            }}
        }}

        function updateChart() {{
            var ref = document.getElementById('refSelect').value;
            var tema = document.getElementById('temaSelect').value;
            
            var regionesActivas = new Set();
            document.querySelectorAll('.region-check:checked').forEach(function(el) {{
                regionesActivas.add(el.value);
            }});

            var paisesActivos = new Set();
            document.querySelectorAll('.pais-check:checked').forEach(function(el) {{
                paisesActivos.add(el.value);
            }});
            
            var newVisibility = [];
            
            for (var i = 0; i < traceMeta.length; i++) {{
                var meta = traceMeta[i];
                if (meta.ref === ref && meta.tema === tema) {{
                    if (meta.type === 'region' && regionesActivas.has(meta.name)) {{
                        newVisibility.push(true);
                    }} else if (meta.type === 'pais' && paisesActivos.has(meta.name)) {{
                        newVisibility.push(true);
                    }} else {{
                        newVisibility.push(false);
                    }}
                }} else {{
                    newVisibility.push(false);
                }}
            }}
            
            Plotly.restyle('myPlotDiv', {{'visible': newVisibility}});
            Plotly.relayout('myPlotDiv', {{
                'title': ref + ' · ' + tema
            }});
            updateCounter();
        }}

        function filtrarPaises() {{
            var input = document.getElementById('buscadorPaises');
            var filter = input.value.toUpperCase();
            var div = document.getElementById('listaPaises');
            var labels = div.getElementsByClassName('pais-item');
            for (var i = 0; i < labels.length; i++) {{
                var txtValue = labels[i].textContent || labels[i].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                    labels[i].style.display = "";
                }} else {{
                    labels[i].style.display = "none";
                }}
            }}
        }}

        function clearAll() {{
            document.querySelectorAll('.region-check, .pais-check').forEach(function(el) {{
                el.checked = false;
            }});
            updateChart();
            updateCounter();
        }}

        window.onload = function() {{
            updateChart();
            updateCounter();
        }};
    </script>
</body>
</html>
"""

with open("dashboard_maestro.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("\n¡Éxito! Dashboard actualizado con Israel por defecto y la nota analítica.")
