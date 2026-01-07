# app.py
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- ELITE APP CONFIG ---
st.set_page_config(page_title="RollSafe", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")

# --- IOS NATIVE STYLE INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600;700;800&display=swap');
    
    .stApp { background-color: #000000; font-family: 'SF Pro Display', -apple-system, sans-serif; }
    header { visibility: hidden; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }

    /* Custom Safety Bar */
    .safety-banner {
        background: linear-gradient(90deg, rgba(255, 69, 58, 0.2) 0%, rgba(255, 69, 58, 0.05) 100%);
        border-left: 5px solid #FF453A;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0 25px 0;
    }

    /* KeepTrucking Style Metric Tiles */
    .tile-container {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }
    .tile {
        background: #1C1C1E;
        border-radius: 20px;
        padding: 20px;
        flex: 1;
        border: 1px solid #2C2C2E;
    }
    .tile-label { color: #8E8E93; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .tile-value { color: #FFFFFF; font-size: 28px; font-weight: 800; margin: 4px 0; }
    .tile-trend { color: #32D74B; font-size: 13px; font-weight: 600; }

    /* Premium iOS Tab System */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1C1C1E;
        border-radius: 14px;
        padding: 5px;
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8E8E93;
        font-weight: 700;
        border: none !important;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3A3A3C !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    /* Action Button - Heavy Blue */
    .stButton>button {
        width: 100%;
        border-radius: 16px;
        height: 62px;
        background: #0A84FF !important;
        color: white !important;
        font-weight: 700;
        font-size: 18px;
        border: none;
        box-shadow: 0 8px 20px rgba(10, 132, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- BRANDING ---
st.markdown('<div style="text-align:center; color:white; font-weight:800; font-size:32px; padding:20px 0; letter-spacing:-1.5px;">RollSafe</div>', unsafe_allow_html=True)

# 1. THE SAFETY GUARDRAIL (Functional Highlight)
st.markdown("""
<div class="safety-banner">
    <div style="color: #FF453A; font-weight: 800; font-size: 12px; letter-spacing: 0.5px;">🛡️ ACTIVE PROTECTION</div>
    <div style="color: white; font-size: 16px; font-weight: 600; margin-top: 4px;">Low Bridge (13' 6") Detected on I-95 N.</div>
</div>
""", unsafe_allow_html=True)

# 2. ELITE TILES (Direct HTML for precision spacing)
st.markdown(f"""
<div class="tile-container">
    <div class="tile">
        <div class="tile-label">Revenue</div>
        <div class="tile-value">$14.2k</div>
        <div class="tile-trend">↑ 12% MTD</div>
    </div>
    <div class="tile">
        <div class="tile-label">Safety Score</div>
        <div class="tile-value" style="color: #0A84FF;">98</div>
        <div class="tile-trend">Top 1% Fleet</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. NATIVE TABS
tab1, tab2, tab3 = st.tabs(["🗺️ DISPATCH", "📂 VAULT", "⛽ IFTA"])

with tab1:
    st.markdown('<div style="background:#1C1C1E; padding:15px; border-radius:20px; border:1px solid #2C2C2E;">', unsafe_allow_html=True)
    st.text_input("📍 Destination", placeholder="Zip, City, or Facility...")
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, tiles="CartoDB dark_matter")
    st_folium(m, height=350, use_container_width=True)
    st.write("")
    if st.button("CALCULATE TRUCK-SAFE ROUTE"):
        st.success("Route Verified for 13' 6\" Clearance.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div style="background:#1C1C1E; padding:20px; border-radius:20px; border:1px solid #2C2C2E;">', unsafe_allow_html=True)
    st.markdown('<div class="tile-label" style="margin-bottom:10px;">Smart Document Sync</div>', unsafe_allow_html=True)
    st.file_uploader("Upload BOL, Med Card, or Permit", type=['png','pdf','jpg'])
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div style="background:#1C1C1E; padding:20px; border-radius:20px; border:1px solid #2C2C2E;">', unsafe_allow_html=True)
    st.markdown('<div class="tile-label">Estimated IFTA (Q1)</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#FF9F0A; font-size:36px; font-weight:800;">$412.00</div>', unsafe_allow_html=True)
    st.caption("Auto-calculated from ELD Logs & Fuel Receipts")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
st.caption("RollSafe Terminal v3.0 • Premium Dispatch OS")
