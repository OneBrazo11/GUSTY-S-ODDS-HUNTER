import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="GUSTY'S GLOBAL HUNTER", layout="wide", page_icon="🌍")

# Estilos CSS para que se vea profesional
st.markdown("""
<style>
    .metric-card {background-color: #1e1e1e; border-radius: 10px; padding: 15px; text-align: center;}
    .big-font {font-size: 20px !important; font-weight: bold;}
    .success-box {padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 10px; border: 1px solid #c3e6cb;}
    .warning-box {padding: 10px; background-color: #f8f9fa; color: #383d41; border-radius: 5px; margin-bottom: 10px; border: 1px solid #d6d8db;}
    .best-price {font-weight: bold; font-size: 1.2em; color: #155724;}
</style>
""", unsafe_allow_html=True)

st.title("🌍 GUSTY'S GLOBAL ODDS HUNTER")
st.markdown("### 🚀 Radar de Apuestas: Todas las casas, una sola búsqueda.")

# --- BARRA LATERAL (API KEY) ---
st.sidebar.header("🔑 Llave de Acceso")
api_key = st.sidebar.text_input("Pega tu API Key nueva:", type="password")

if not api_key:
    st.warning("👈 Ingresa tu API Key en la barra lateral para activar el sistema.")
    st.stop()

# --- FUNCIONES DEL SISTEMA ---

def get_quota_status(key):
    """Revisa tus créditos sin gastar nada extra (lee los headers)"""
    try:
        url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
        r = requests.get(url)
        headers = r.headers
        remaining = headers.get("x-requests-remaining", "0")
        used = headers.get("x-requests-used", "0")
        return remaining, used
    except:
        return "?", "?"

def get_active_sports(key):
    """Descarga la lista de deportes activos hoy"""
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={key}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []

def get_odds_global(key, sport, market):
    """
    ESTRATEGIA DE AHORRO MÁXIMO:
    Pedimos regions='us,uk,eu,au' en UNA sola llamada.
    Esto trae Pinnacle, Bet365, Bovada, 1xBet, Unibet, etc. juntas.
    Costo: Solo gastas cuota por deporte, no por región.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        'apiKey': key,
        'regions': 'us,uk,eu,au', # <--- EL TRUCO: Pedimos todo el planeta de una vez
        'markets': market,
        'oddsFormat': 'decimal',
        # Al no filtrar bookmakers, la API nos da TODO lo que tenga disponible
    }
    try:
        r = requests.get(url, params=params)
        if r.status_code != 200:
            return None, r.text
        return r.json(), None
    except Exception as e:
        return None, str(e)

# --- PANEL DE CONTROL DE CRÉDITOS ---
rem, used = get_quota_status(api_key)
col1, col2, col3 = st.columns(3)
col1.metric("💰 Créditos Restantes", rem)
col2.metric("📉 Créditos Usados", used)
col3.info("💡 Consejo: Cada vez que presionas 'BUSCAR', gastas créditos. ¡Úsalo con sabiduría!")

if str(rem) == "0":
    st.error("⛔ SALDO AGOTADO. Debes crear una cuenta nueva en The-Odds-API.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("1. Selección de Liga")

# Cargar deportes
sports_data = get_active_sports(api_key)
if not sports_data:
    st.error("Error cargando deportes. Revisa si tu API Key es válida.")
    st.stop()

# Crear diccionario {Nombre: Key}
sport_options = {s['title']: s['key'] for s in sports_data}

# Filtro de texto para encontrar rápido
search_filter = st.sidebar.text_input("🔍 Filtrar deporte (Ej: NBA, Soccer, Tennis):")
filtered_options = list(sport_options.keys())

if search_filter:
    filtered_options = [x for x in filtered_options if search_filter.lower() in x.lower()]

if not filtered_options:
    st.sidebar.warning("No se encontraron deportes con ese nombre.")
    st.stop()

selected_sport_name = st.sidebar.selectbox("Elige la Liga:", filtered_options)
selected_sport_key = sport_options[selected_sport_name]

# Selector de Mercado
st.sidebar.subheader("2. Tipo de Apuesta")
market_display = st.sidebar.selectbox("Mercado:", ["Ganador del Partido (H2H)", "Hándicap (Spread)", "Totales (Over/Under)"])

# Traducción para la API
market_api = "h2h"
if "Hándicap" in market_display: market_api = "spreads"
if "Totales" in market_display: market_api = "totals"

# --- BOTÓN DE DISPARO ---
st.markdown("---")
st.header(f"📡 Escáner Global: {selected_sport_name}")
st.caption("Al presionar buscar, rastrearemos Pinnacle, Bet365, Bovada, 1xBet y más al mismo tiempo.")

if st.button("🚀 BUSCAR OPORTUNIDADES AHORA", type="primary"):
    
    with st.spinner("Conectando con servidores globales..."):
        data, error = get_odds_global(api_key, selected_sport_key, market_api)

        if error:
            st.error(f"Error en la API: {error}")
        elif not data:
            st.warning("La API respondió correctamente, pero no hay cuotas activas para este deporte ahora mismo.")
        else:
            st.success(f"¡Éxito! Se encontraron {len(data)} eventos con cuotas activas.")
            
            # --- PROCESAMIENTO DE PARTIDOS ---
            for game in data:
                home = game['home_team']
                away = game['away_team']
                # Formato de fecha simple
                start_time = game['commence_time'].replace("T", " ").replace("Z", " UTC")
                
                # Agrupamos las cuotas de todas las casas del mundo
                # Estructura: {'Opción A': [{'Casa': 'Pinnacle', 'Cuota': 1.95}, ...]}
                odds_pool = {} 

                for book in game['bookmakers']:
                    book_name = book['title']
                    for market in book['markets']:
                        if market['key'] == market_api:
                            for outcome in market['outcomes']:
                                name = outcome['name']
                                price = outcome['price']
                                point = outcome.get('point', '')

                                # Etiqueta (Ej: "Lakers -5.5" o "Real Madrid")
                                if point:
                                    label = f"{name} ({point})"
                                else:
                                    label = name
                                
                                if label not in odds_pool:
                                    odds_pool[label] = []
                                odds_pool[label].append({'Casa': book_name, 'Cuota': price})

                # --- VISUALIZACIÓN ---
                if odds_pool:
                    with st.expander(f"⚽/🏀 {home} vs {away} | {start_time}", expanded=True):
                        
                        # Creamos columnas dinámicas según cuantas opciones haya (Local/Visita o Local/Empate/Visita)
                        cols = st.columns(len(odds_pool))
                        
                        # Analizamos cada opción
                        for idx, (selection, entries) in enumerate(odds_pool.items()):
                            df = pd.DataFrame(entries)
                            
                            if df.empty: continue
                            
                            # Estadísticas básicas
                            max_odd = df['Cuota'].max()
                            avg_odd = df['Cuota'].mean()
                            
                            # Encontrar las mejores casas
                            best_books_df = df[df['Cuota'] == max_odd]
                            best_books_list = best_books_df['Casa'].tolist()
                            
                            # Formato de lista de casas (Max 3)
                            best_books_str = ", ".join(best_books_list[:3])
                            if len(best_books_list) > 3: best_books_str += " y más..."

                            # ¿Hay Valor? (Si la mejor cuota es 4% superior al promedio)
                            is_value = max_odd > (avg_odd * 1.04)
                            
                            with cols[idx % len(cols)]:
                                st.markdown(f"**{selection}**")
                                if is_value:
                                    # Caja VERDE para valor
                                    html_box = f"""
                                    <div class='success-box'>
                                        <span class='best-price'>💎 {max_odd}</span><br>
                                        <small>en {best_books_str}</small><br>
                                        <small style='color:green'>+{((max_odd-avg_odd)/avg_odd)*100:.1f}% vs Promedio</small>
                                    </div>
                                    """
                                    st.markdown(html_box, unsafe_allow_html=True)
                                else:
                                    # Caja GRIS normal
                                    html_box = f"""
                                    <div class='warning-box'>
                                        <span style='font-weight:bold'>{max_odd}</span><br>
                                        <small>en {best_books_str}</small>
                                    </div>
                                    """
                                    st.markdown(html_box, unsafe_allow_html=True)

                        # Tabla completa desplegable al final
                        st.markdown("---")
                        st.caption("📋 Comparativa Detallada (Todas las casas detectadas):")
                        
                        all_rows = []
                        for sel, entries in odds_pool.items():
                            for e in entries:
                                all_rows.append({'Selección': sel, 'Casa': e['Casa'], 'Cuota': e['Cuota']})
                        
                        if all_rows:
                            df_full = pd.DataFrame(all_rows)
                            try:
                                # Pivotar para ver fácil: Casas en filas, Opciones en columnas
                                df_pivot = df_full.pivot(index='Casa', columns='Selección', values='Cuota')
                                st.dataframe(df_pivot.style.highlight_max(axis=0, color='#d4edda'), use_container_width=True)
                            except:
                                st.dataframe(df_full)
