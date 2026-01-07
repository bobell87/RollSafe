# app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- ELITE UI CONFIGURATION ---
st.set_page_config(page_title="RollSafe", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")

# Injecting Native iOS Styles (The "KeepTrucking" Look)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600;800&display=swap');
    
    .stApp { background-color: #000000; font-family: -apple-system, sans-serif; }
    
    /* Pulsating Safety Alert */
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 69, 58, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(255, 69, 58, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 69, 58, 0); } }
    .safety-card {
        background: rgba(255, 69, 58, 0.15); border: 2px solid #FF453A;
        border-radius: 20px; padding: 20px; margin-bottom: 25px;
        animation: pulse 2s infinite;
    }

    /* Elite Glassmorphism Cards */
    .glass-card {
        background: #1C1C1E; border: 1px solid #2C2C2E;
        border-radius: 24px; padding: 24px; margin-bottom: 20px;
    }
    
    .metric-label { color: #8E8E93; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #FFFFFF; font-size: 32px; font-weight: 800; margin-top: 5px; }
    .metric-sub { color: #34C759; font-size: 14px; font-weight: 600; }

    /* Bottom Navigation Bar Simulation */
    .nav-bar {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: rgba(28, 28, 30, 0.95); backdrop-filter: blur(15px);
        border-top: 1px solid #2C2C2E; padding: 15px;
        display: flex; justify-content: space-around; z-index: 100;
    }

    /* iOS Style Buttons */
    .stButton>button {
        width: 100%; border-radius: 16px; height: 60px;
        background: #0A84FF !important; color: white !important;
        font-weight: 700; font-size: 18px; border: none;
        transition: transform 0.1s ease;
    }
    .stButton>button:active { transform: scale(0.97); }
</style>
""", unsafe_allow_html=True)

# --- APP LOGIC ---
st.markdown('<div style="text-align:center; color:white; font-weight:800; font-size:24px; padding:10px;">RollSafe</div>', unsafe_allow_html=True)

# 1. Pulsating Alert Center
st.markdown("""
<div class="safety-card">
    <div style="color: #FF453A; font-weight: 800; font-size: 14px; margin-bottom: 4px;">⚠️ CRITICAL GUARDRAIL</div>
    <div style="color: white; font-size: 16px; font-weight: 600;">Low Bridge: 13' 6" on I-95 N. Re-route advised for Unit T-12.</div>
</div>
""", unsafe_allow_html=True)

# 2. Main Dashboard Metrics
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="glass-card"><div class="metric-label">Revenue MTD</div><div class="metric-value">$14.2k</div><div class="metric-sub">↑ 12% vs last mo</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="glass-card"><div class="metric-label">Compliance</div><div class="metric-value">Elite</div><div class="metric-sub" style="color:#0A84FF">Audit Ready</div></div>', unsafe_allow_html=True)

# 3. Interactive Planner (The Turnkey Part)
tab1, tab2, tab3 = st.tabs(["🗺️ DISPATCH", "📂 VAULT", "⛽ IFTA"])

with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    dest = st.text_input("📍 Next Destination", placeholder="Search Address or Truck Stop...")
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, tiles="CartoDB dark_matter")
    st_folium(m, height=350, use_container_width=True)
    if st.button("CALCULATE TRUCK-SAFE ROUTE"):
        st.success("Analyzing 452 Bridge Clearances... Route Verified.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">OCR Smart Scan</div>', unsafe_allow_html=True)
    up = st.file_uploader("Upload BOL/RateCon", type=['png','pdf','jpg'])
    if up:
        st.info("Extracting Load ID: LD-7781 | Weight: 42,000 lbs")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Projected IFTA Tax</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-value" style="color:#FF9F0A">$412.00</div>', unsafe_allow_html=True)
    st.caption("Based on 1,240 miles in IL, IN, and OH (Simulated)")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
st.write("") # Spacer for bottom nav
st.caption("RollSafe Terminal • v2026.1.1 • rollsafe.app")
