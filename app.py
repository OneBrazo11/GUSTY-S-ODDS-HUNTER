import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE LA PÁGINA (ICONO CAMBIADO A COHETE) ---
st.set_page_config(page_title="GLOBAL ODDS HUNTER", layout="wide", page_icon="🚀")

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

st.title("🚀 GLOBAL ODDS HUNTER")
st.markdown("### 📡 Radar de Apuestas: WINNER, HANDICAP, TOTALS, EVEN/ODD Y MÁS.")

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
col1, col2, col3 = st.columns(
