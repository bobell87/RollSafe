# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta, date
import re
import io
import json
import math
from typing import Dict, Any, Tuple, List, Optional

# --- BRANDING & UI CONFIG ---
st.set_page_config(
    page_title="RollSafe",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# High-End Mobile CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Sleek Apple-style Cards */
    div[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* Professional Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }

    /* iOS Style Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 16px;
        height: 56px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white !important;
        border: none;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    
    /* Metrics / KPIs */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #818cf8 !important;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- UTILITIES & LOGIC ---
def now_ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simulate_truck_safe_checks(origin, dest, height_ft):
    # Simulated bridge & safety logic
    dist = 450.0 # Placeholder distance
    sim_min_bridge = 14.2
    margin = sim_min_bridge - height_ft
    risk = "OK" if margin > 1.0 else "HIGH"
    return {"risk": risk, "margin": round(margin, 1), "dist": dist}

# --- APP LAYOUT ---
# Header with Logo Placeholder
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("## 🛡️") # Icon placeholder for RollSafe Logo
with col2:
    st.title("RollSafe")
    st.markdown("*Premium Dispatch & Compliance OS*")

st.divider()

# Main Dashboard
tab1, tab2, tab3 = st.tabs(["📊 COMMAND", "🗺️ PLANNER", "📁 DOCUMENTS"])

with tab1:
    m1, m2, m3 = st.columns(3)
    m1.metric("Active Trips", "3", "+1")
    m2.metric("Compliance", "98%", "Safe")
    m3.metric("Revenue (MTD)", "$12,450")
    
    st.markdown("### 🔔 Safety Alerts")
    st.warning("Annual DOT Inspection due in 12 days for Unit T-12.")

with tab2:
    st.markdown("### Route Planner")
    origin = st.text_input("Origin", "Chicago, IL")
    destination = st.text_input("Destination", "Dallas, TX")
    height = st.number_input("Truck Height (ft)", value=13.6)
    
    if st.button("RUN SAFETY GUARDRAIL"):
        res = simulate_truck_safe_checks(origin, destination, height)
        if res["risk"] == "OK":
            st.success(f"ROUTE SAFE: {res['margin']}ft Clearance Detected.")
        else:
            st.error("HIGH RISK: Restricted Bridge Height Detected on this corridor.")
            
    # Map
    m = folium.Map(location=[39.8, -98.5], zoom_start=4)
    st_folium(m, height=350, use_container_width=True)

with tab3:
    st.markdown("### Digital Folder")
    uploaded_file = st.file_uploader("Drop BOL or Rate Con here", type=['png', 'pdf', 'jpg'])
    if uploaded_file:
        st.info("AI Extracting Data... (Load ID: LD-9928 Detected)")
        st.success("Document Safely Stored & Indexed.")

st.caption("© 2026 RollSafe.app | Simulated Compliance Data")
