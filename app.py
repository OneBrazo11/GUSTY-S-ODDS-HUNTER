import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="GUSTY'S GLOBAL HUNTER", layout="wide", page_icon="🏀")

# Estilos CSS
st.markdown("""
<style>
    .metric-card {background-color: #1e1e1e; border-radius: 10px; padding: 15px; text-align: center;}
    .big-font {font-size: 20px !important; font-weight: bold;}
    .success-box {padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 10px; border: 1px solid #c3e6cb;}
    .warning-box {padding: 10px; background-color: #f8f9fa; color: #383d41; border-radius: 5px; margin-bottom: 10px; border: 1px solid #d6d8db;}
    .best-price {font-weight: bold; font-size: 1.2em; color: #155724;}
</style>
""", unsafe_allow_html=True)

st.title("🏀 GUSTY'S GLOBAL ODDS HUNTER")
st.markdown("### 🚀 Radar de Apuestas: NBA, Cuartos, Mitades y Más.")

# --- BARRA LATERAL (API KEY) ---
st.sidebar.header("🔑 Llave de Acceso")
api_key = st.sidebar.text_input("Tu API Key:", type="password")

if not api_key:
    st.warning("👈 Ingresa tu API Key en la barra lateral.")
    st.stop()

# --- FUNCIONES ---

def get_quota_status(key):
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
    Busca en USA, UK, EU y AU en una sola llamada.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        'apiKey': key,
        'regions': 'us,uk,eu,au', # Todo el mundo
        'markets': market,        # El mercado específico (ej: spreads_h1)
        'oddsFormat': 'decimal',
    }
    try:
        r = requests.get(url, params=params)
        if r.status_code != 200:
            return None, r.text
        return r.json(), None
    except Exception as e:
        return None, str(e)

# --- PANEL DE CRÉDITOS ---
rem, used = get_quota_status(api_key)
col1, col2, col3 = st.columns(3)
col1.metric("💰 Créditos Restantes", rem)
col2.metric("📉 Créditos Usados", used)
col3.info("💡 Consejo: Usa el selector de Periodo para gastar créditos solo en lo que necesitas.")

if str(rem) == "0":
    st.error("⛔ SALDO AGOTADO. Crea una cuenta nueva.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("1. Liga")

# Cargar deportes
sports_data = get_active_sports(api_key)
if not sports_data:
    st.error("Error cargando deportes.")
    st.stop()

sport_options = {s['title']: s['key'] for s in sports_data}

# Filtro rápido
search_filter = st.sidebar.text_input("🔍 Filtrar (Ej: NBA):")
filtered_options = list(sport_options.keys())

if search_filter:
    filtered_options = [x for x in filtered_options if search_filter.lower() in x.lower()]

if not filtered_options:
    st.sidebar.warning("No encontrado.")
    st.stop()

selected_sport_name = st.sidebar.selectbox("Elige:", filtered_options)
selected_sport_key = sport_options[selected_sport_name]

# --- SELECTORES DE MERCADO Y PERIODO (NUEVO) ---
st.sidebar.subheader("2. Estrategia de Caza")

# Tipo de apuesta
bet_type = st.sidebar.selectbox("Tipo de Apuesta:", ["Ganador (Moneyline)", "Hándicap (Spread)", "Totales (Over/Under)"])

# Periodo (AQUÍ ESTÁ LA MAGIA)
period_type = st.sidebar.selectbox("Periodo:", [
    "Partido Completo", 
    "1ra Mitad (1H)", 
    "2da Mitad (2H)", 
    "1er Cuarto (1Q)", 
    "2do Cuarto (2Q)", 
    "3er Cuarto (3Q)", 
    "4to Cuarto (4Q)"
])

# Construcción de la Key para la API
# 1. Prefijo
api_market = "h2h"
if "Hándicap" in bet_type: api_market = "spreads"
if "Totales" in bet_type: api_market = "totals"

# 2. Sufijo (El periodo)
if "1ra Mitad" in period_type: api_market += "_h1"
elif "2da Mitad" in period_type: api_market += "_h2"
elif "1er Cuarto" in period_type: api_market += "_q1"
elif "2do Cuarto" in period_type: api_market += "_q2"
elif "3er Cuarto" in period_type: api_market += "_q3"
elif "4to Cuarto" in period_type: api_market += "_q4"
# Si es "Partido Completo", no se añade sufijo.

st.sidebar.info(f"🔎 Buscando mercado: **{api_market}**")

# --- BOTÓN DE ACCIÓN ---
st.markdown("---")
st.header(f"📡 Escáner: {selected_sport_name} - {period_type}")

if st.button("🚀 BUSCAR CUOTAS", type="primary"):
    
    with st.spinner(f"Rastreando {bet_type} para {period_type} en todo el mundo..."):
        data, error = get_odds_global(api_key, selected_sport_key, api_market)

        if error:
            st.error(f"Error API: {error}")
        elif not data:
            st.warning(f"No hay cuotas activas para '{period_type}' en este momento. Intenta con Partido Completo.")
        else:
            st.success(f"¡Encontrados {len(data)} eventos!")
            
            for game in data:
                home = game['home_team']
                away = game['away_team']
                start_time = game['commence_time'].replace("T", " ").replace("Z", " UTC")
                
                odds_pool = {} 

                for book in game['bookmakers']:
                    book_name = book['title']
                    for market in book['markets']:
                        # Comparamos con la key exacta construida (ej: spreads_q1)
                        if market['key'] == api_market:
                            for outcome in market['outcomes']:
                                name = outcome['name']
                                price = outcome['price']
                                point = outcome.get('point', '')

                                if point:
                                    label = f"{name} ({point})"
                                else:
                                    label = name
                                
                                if label not in odds_pool:
                                    odds_pool[label] = []
                                odds_pool[label].append({'Casa': book_name, 'Cuota': price})

                if odds_pool:
                    with st.expander(f"{home} vs {away} | {period_type}", expanded=True):
                        cols = st.columns(len(odds_pool))
                        
                        for idx, (selection, entries) in enumerate(odds_pool.items()):
                            df = pd.DataFrame(entries)
                            if df.empty: continue
                            
                            max_odd = df['Cuota'].max()
                            avg_odd = df['Cuota'].mean()
                            
                            best_books_df = df[df['Cuota'] == max_odd]
                            best_books_list = best_books_df['Casa'].tolist()
                            best_books_str = ", ".join(best_books_list[:3])
                            if len(best_books_list) > 3: best_books_str += "..."

                            # Valor: > 4% sobre promedio
                            is_value = max_odd > (avg_odd * 1.04)
                            
                            with cols[idx % len(cols)]:
                                st.markdown(f"**{selection}**")
                                if is_value:
                                    html_box = f"""
                                    <div class='success-box'>
                                        <span class='best-price'>💎 {max_odd}</span><br>
                                        <small>{best_books_str}</small><br>
                                        <small style='color:green'>VALOR DETECTADO</small>
                                    </div>
                                    """
                                    st.markdown(html_box, unsafe_allow_html=True)
                                else:
                                    html_box = f"""
                                    <div class='warning-box'>
                                        <span style='font-weight:bold'>{max_odd}</span><br>
                                        <small>{best_books_str}</small>
                                    </div>
                                    """
                                    st.markdown(html_box, unsafe_allow_html=True)

                        st.caption("Todas las casas:")
                        all_rows = []
                        for sel, entries in odds_pool.items():
                            for e in entries:
                                all_rows.append({'Selección': sel, 'Casa': e['Casa'], 'Cuota': e['Cuota']})
                        
                        if all_rows:
                            df_full = pd.DataFrame(all_rows)
                            try:
                                df_pivot = df_full.pivot(index='Casa', columns='Selección', values='Cuota')
                                st.dataframe(df_pivot.style.highlight_max(axis=0, color='#d4edda'), use_container_width=True)
                            except:
                                st.dataframe(df_full)
