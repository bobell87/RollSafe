# app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- APP CONFIG ---
st.set_page_config(page_title="RollSafe", page_icon="🛡️", layout="centered")

# --- IOS PROFESSIONAL CSS ---
st.markdown("""
<style>
    /* Professional Dark Mode Base */
    .stApp {
        background-color: #000000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* High-Contrast iOS Header */
    .header {
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF;
        padding-top: 20px;
        letter-spacing: -1px;
    }

    /* Red Alert Card - Unmissable */
    .safety-alert {
        background: rgba(255, 69, 58, 0.2);
        border: 2px solid #FF453A;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
    }
    .alert-title {
        color: #FF453A;
        font-weight: 800;
        font-size: 18px;
        margin-bottom: 5px;
    }
    .alert-text {
        color: #FFFFFF;
        font-size: 15px;
    }

    /* Glass Activity Cards */
    .ios-card {
        background: #1C1C1E;
        border-radius: 24px;
        padding: 20px;
        border: 1px solid #2C2C2E;
        margin-bottom: 15px;
    }
    .card-label {
        color: #8E8E93;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .card-value {
        color: #0A84FF;
        font-size: 32px;
        font-weight: 800;
    }

    /* Native iOS Bottom-style Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1C1C1E;
        padding: 5px;
        border-radius: 15px;
        display: flex;
        justify-content: space-around;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8E8E93;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: #3A3A3C !important;
        border-radius: 10px !important;
    }

    /* Clean Blue Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 60px;
        background-color: #0A84FF !important;
        color: white !important;
        font-weight: 700;
        font-size: 18px;
        border: none;
        box-shadow: 0 4px 12px rgba(10, 132, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- APP TOP BAR ---
st.markdown('<div class="header">RollSafe</div>', unsafe_allow_html=True)

# --- CRITICAL SAFETY ALERT ---
st.markdown("""
<div class="safety-alert">
    <div class="alert-title">🚨 BRIDGE WARNING</div>
    <div class="alert-text">Low clearance (13' 6") detected on planned route: I-95 Northbound. Unit T-12 requires re-route.</div>
</div>
""", unsafe_allow_html=True)

# --- MAIN NAV ---
tab1, tab2, tab3 = st.tabs(["📊 STATUS", "🗺️ MAP", "📂 VAULT"])

with tab1:
    st.write("")
    # Status Row
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="ios-card"><div class="card-label">Active Loads</div><div class="card-value">02</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="ios-card"><div class="card-label">Compliance</div><div class="card-value">100%</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="ios-card"><div class="card-label">Next Inspection</div><div class="card-value" style="color:#FF9F0A">12 Days</div></div>', unsafe_allow_html=True)

with tab2:
    st.write("")
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.text_input("📍 Search Destination...", placeholder="Enter City or Zip")
    # Map
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=10, tiles="CartoDB dark_matter")
    st_folium(m, height=300, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("GENERATE SAFE ROUTE"):
        st.balloons()

with tab3:
    st.write("")
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">Document Scan</div>', unsafe_allow_html=True)
    st.file_uploader("Upload BOL, RateCon, or Medical Card", type=['pdf', 'jpg', 'png'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="ios-card"><div class="card-label">Recent Files</div><div style="color:white; padding-top:10px;">📄 RateCon_7781.pdf<br>📄 BOL_Chicago_Indy.jpg</div></div>', unsafe_allow_html=True)

st.divider()
st.caption("RollSafe Terminal v2.5 | Active Connection: rollsafe.app")
