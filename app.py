# app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- ELITE APP CONFIG ---
st.set_page_config(page_title="RollSafe", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")

# --- IOS & KEEPTRUCKING STYLE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;700;800&display=swap');
    
    /* Pure Black Background like iOS Dark Mode */
    .stApp { background-color: #000000; font-family: -apple-system, sans-serif; }
    header { visibility: hidden; }
    
    /* Pulsating Safety Alert - The "Elite" Feature */
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 69, 58, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(255, 69, 58, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 69, 58, 0); } }
    .safety-alert {
        background: rgba(255, 69, 58, 0.1); border: 1px solid #FF453A;
        border-radius: 18px; padding: 16px; margin-bottom: 20px;
        animation: pulse 2s infinite;
    }

    /* Glassmorphism Action Cards */
    .glass-card {
        background: #1C1C1E; border: 1px solid #2C2C2E;
        border-radius: 20px; padding: 20px; margin-bottom: 12px;
    }
    
    .label { color: #8E8E93; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .value { color: #FFFFFF; font-size: 28px; font-weight: 800; }
    .sub-text { color: #34C759; font-size: 13px; font-weight: 600; }

    /* Custom Mobile Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1C1C1E; border-radius: 12px; padding: 4px;
        display: flex; justify-content: space-around;
    }
    .stTabs [data-baseweb="tab"] { color: #8E8E93; font-weight: 700; }
    .stTabs [aria-selected="true"] { color: #FFFFFF !important; background-color: #3A3A3C !important; border-radius: 8px !important; }

    /* iOS Blue Button */
    .stButton>button {
        width: 100%; border-radius: 14px; height: 58px;
        background-color: #0A84FF !important; color: white !important;
        font-weight: 700; font-size: 17px; border: none;
    }
</style>
""", unsafe_allow_html=True)

# --- APP UI ---
st.markdown('<div style="text-align:center; color:white; font-weight:800; font-size:26px; padding:15px; letter-spacing:-1px;">RollSafe</div>', unsafe_allow_html=True)

# 1. Safety Alert (Priority 1)
st.markdown("""
<div class="safety-alert">
    <div style="color: #FF453A; font-weight: 800; font-size: 13px;">🛡️ SAFETY GUARDRAIL</div>
    <div style="color: white; font-size: 15px; font-weight: 600; margin-top: 4px;">Bridge Warning: 13' 6" on I-95 N. Unit T-12 re-route suggested.</div>
</div>
""", unsafe_allow_html=True)

# 2. Key Metrics Row
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="glass-card"><div class="label">Revenue</div><div class="value">$14.2k</div><div class="sub-text">↑ 12%</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="glass-card"><div class="label">Compliance</div><div class="value" style="color:#0A84FF">Elite</div><div class="sub-text">Audit Ready</div></div>', unsafe_allow_html=True)

# 3. iOS Tab Navigation
tab1, tab2, tab3 = st.tabs(["🗺️ DISPATCH", "📂 VAULT", "⛽ IFTA"])

with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.text_input("📍 Destination", placeholder="Enter Zip or City...")
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, tiles="CartoDB dark_matter")
    st_folium(m, height=300, use_container_width=True)
    st.write("")
    if st.button("RUN TRUCK-SAFE ROUTE"):
        st.success("Analysis Complete: 0 Clearance Risks Detected.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Smart Folder</div>', unsafe_allow_html=True)
    up = st.file_uploader("Upload BOL or RateCon", type=['png','pdf','jpg'])
    if up:
        st.info("AI Analysis: Load ID LD-7781 Detected.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="glass-card"><div class="label">IFTA Tax Owed</div><div class="value" style="color:#FF9F0A">$412.00</div><div class="sub-text" style="color:#8E8E93">Based on Q1 Miles</div></div>', unsafe_allow_html=True)

st.caption("RollSafe Terminal v2.5 • rollsafe.app")
