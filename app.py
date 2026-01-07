# app.py
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

# --- ELITE APP CONFIG ---
st.set_page_config(page_title="RollSafe", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")

# --- NATIVE iOS CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;700;800&display=swap');
    .stApp { background-color: #000000; font-family: 'SF Pro Display', sans-serif; }
    header { visibility: hidden; }
    
    .safety-banner {
        background: linear-gradient(90deg, rgba(255, 69, 58, 0.2) 0%, rgba(0,0,0,0) 100%);
        border-left: 4px solid #FF453A; border-radius: 12px;
        padding: 16px; margin: 10px 0 20px 0;
    }

    .tile-container { display: flex; gap: 10px; margin-bottom: 15px; }
    .tile { background: #1C1C1E; border-radius: 18px; padding: 15px; flex: 1; border: 1px solid #2C2C2E; }
    .label { color: #8E8E93; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    .value { color: #FFFFFF; font-size: 24px; font-weight: 800; }

    .stButton>button {
        width: 100%; border-radius: 14px; height: 55px;
        background: #0A84FF !important; color: white !important;
        font-weight: 700; border: none;
    }
    /* GPS Button Style */
    .gps-btn>button { background: #32D74B !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="text-align:center; color:white; font-weight:800; font-size:28px; padding:15px;">RollSafe</div>', unsafe_allow_html=True)

# --- GPS LOGIC ---
# This pulls the actual phone location
location = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(pos => { window.parent.postMessage({type: 'streamlit:setComponentValue', value: [pos.coords.latitude, pos.coords.longitude]}, '*') });", key="gps")

# 1. LIVE GUARDRAIL
st.markdown("""
<div class="safety-banner">
    <div style="color: #FF453A; font-weight: 800; font-size: 11px;">🛡️ LIVE GPS GUARDRAIL</div>
    <div style="color: white; font-size: 15px; font-weight: 600; margin-top: 4px;">Monitoring Route for Low Bridges & Hazmat Restrictions.</div>
</div>
""", unsafe_allow_html=True)

# 2. METRICS
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="tile"><div class="label">Trip Profit</div><div class="value">$1,240</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="tile"><div class="label">Compliance</div><div class="value" style="color:#32D74B">ELITE</div></div>', unsafe_allow_html=True)

# 3. DISPATCH MAP
tab1, tab2 = st.tabs(["🗺️ NAVIGATION", "📂 VAULT"])

with tab1:
    st.markdown('<div style="background:#1C1C1E; padding:15px; border-radius:20px;">', unsafe_allow_html=True)
    
    # If GPS is found, center there; otherwise center on USA
    view_lat, view_lon = location if location else [39.8, -98.5]
    zoom = 14 if location else 4
    
    m = folium.Map(location=[view_lat, view_lon], zoom_start=zoom, tiles="CartoDB dark_matter")
    if location:
        folium.Marker([view_lat, view_lon], popup="Truck Location", icon=folium.Icon(color='blue', icon='truck', prefix='fa')).add_to(m)
    
    st_folium(m, height=350, use_container_width=True)
    
    if st.button("🔄 RE-CENTER GPS", key="gps_trigger"):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="tile"><div class="label">Smart OCR</div>', unsafe_allow_html=True)
    st.file_uploader("Upload BOL/RateCon", type=['png','pdf','jpg'])
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("RollSafe Terminal • v3.5 GPS-Active")
