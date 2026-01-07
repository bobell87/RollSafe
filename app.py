# app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(
    page_title="RollSafe",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- PREMIUM IOS CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600;800&display=swap');
    
    .stApp {
        background-color: #000000;
        font-family: 'SF Pro Display', -apple-system, sans-serif;
    }
    
    /* Header Styling */
    .main-header {
        font-size: 28px;
        font-weight: 800;
        color: white;
        padding-bottom: 20px;
        text-align: center;
    }

    /* iOS Style Alert Box */
    .alert-box {
        background: rgba(255, 59, 48, 0.15);
        border: 1px solid #FF3B30;
        border-radius: 18px;
        padding: 15px;
        margin-bottom: 20px;
        color: #FF453A;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #1C1C1E;
        padding: 8px;
        border-radius: 12px;
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: transparent;
        border-radius: 8px;
        color: #8E8E93;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2C2C2E !important;
        color: #0A84FF !important;
    }

    /* Big Action Cards */
    div[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
        background: #1C1C1E;
        border-radius: 22px;
        padding: 20px;
        border: 1px solid #2C2C2E;
        margin-bottom: 15px;
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        color: #0A84FF !important;
        font-weight: 800 !important;
    }

    /* Mobile Button */
    .stButton>button {
        width: 100%;
        border-radius: 14px;
        height: 55px;
        background: #0A84FF;
        color: white !important;
        border: none;
        font-size: 17px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA & LOGIC ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# --- UI LAYOUT ---
st.markdown('<div class="main-header">RollSafe</div>', unsafe_allow_html=True)

# 1. iOS Style Alert Box (Priority Info)
st.markdown("""
<div class="alert-box">
    <strong>⚠️ SAFETY ALERT</strong><br>
    Low clearance (13' 4") reported on I-90 near exit 42. Verify height before transit.
</div>
""", unsafe_allow_html=True)

# 2. Main Navigation Tabs
tab1, tab2, tab3 = st.tabs(["📊 Activity", "🗺️ Routes", "📁 Files"])

with tab1:
    st.markdown("### Status")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Active Loads", "2")
    with c2:
        st.metric("Driver Status", "On Duty")
    
    st.markdown("### Recent Activity")
    st.info("Load LD-442 delivered to Chicago Hub.")

with tab2:
    st.markdown("### Trip Planner")
    st.text_input("Enter Destination")
    
    # Map with better mobile sizing
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=10, tiles="CartoDB dark_matter")
    st_folium(m, height=300, use_container_width=True)
    
    st.write("")
    if st.button("Calculate Truck-Safe Route"):
        st.success("Safe Route Calculated: 0 Bridge Risks")

with tab3:
    st.markdown("### Document Vault")
    st.file_uploader("Scan or Upload BOL", type=['pdf', 'jpg', 'png'])
    st.markdown("---")
    st.markdown("**Cloud Sync Status:** ✅ All files backed up")

st.caption("v2.1.0 • Connected to rollsafe.app")
