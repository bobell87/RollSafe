# app.py
# Rollsaf(e) v2 — Free-stack Streamlit prototype
# Run:
#   pip install streamlit pandas numpy altair folium streamlit-folium
#   streamlit run app.py
#
# Notes:
# - Uses OpenStreetMap tiles (free) via Folium.
# - OCR/extraction is LOCAL-ONLY and best-effort; if OCR libs aren't available, it falls back to heuristic parsing.
# - "Truck-safe routing", bridge heights, hazmat rules, and state mileage attribution are SIMULATED (clearly labeled).

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

# -----------------------------
# App setup + theme CSS
# -----------------------------
st.set_page_config(
    page_title="RollSafe — Dispatch + Compliance OS (Free Prototype)",
    page_icon="🛻",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root {
  --bg: #0b1220;
  --panel: rgba(255,255,255,0.06);
  --panel2: rgba(255,255,255,0.08);
  --stroke: rgba(255,255,255,0.10);
  --text: rgba(255,255,255,0.92);
  --muted: rgba(255,255,255,0.70);
  --good: #42f58d;
  --warn: #ffd166;
  --bad: #ff5c7a;
  --brand: #7aa2ff;
  --brand2: #9bf6ff;
  --chip: rgba(122,162,255,0.15);
  --shadow: 0 10px 30px rgba(0,0,0,0.35);
  --radius: 18px;
}
html, body, [class*="css"]  { color: var(--text); }
.stApp {
  background:
    radial-gradient(1200px 700px at 10% 10%, rgba(122,162,255,0.23), transparent 55%),
    radial-gradient(900px 600px at 85% 30%, rgba(155,246,255,0.18), transparent 50%),
    radial-gradient(900px 700px at 40% 95%, rgba(255,92,122,0.14), transparent 55%),
    linear-gradient(180deg, #060a14 0%, #080d1a 30%, #070b16 100%);
}
.block-container { padding-top: 1.2rem; padding-bottom: 2.0rem; }
.small-muted { color: var(--muted); font-size: 0.92rem; }
.hr { height: 1px; background: var(--stroke); margin: 0.75rem 0 1.0rem; border-radius: 12px; }

.card {
  background: var(--panel);
  border: 1px solid var(--stroke);
  border-radius: var(--radius);
  padding: 1.0rem 1.0rem;
  box-shadow: var(--shadow);
}
.card2 {
  background: var(--panel2);
  border: 1px solid var(--stroke);
  border-radius: var(--radius);
  padding: 1.0rem 1.0rem;
  box-shadow: var(--shadow);
}
.h1 {
  font-size: 1.55rem; font-weight: 800; letter-spacing: -0.02em;
}
.h2 {
  font-size: 1.20rem; font-weight: 750; letter-spacing: -0.01em;
}
.badge {
  display: inline-block; padding: 0.22rem 0.55rem; margin-right: 0.35rem;
  border-radius: 999px; border: 1px solid var(--stroke); background: var(--chip);
  font-size: 0.85rem; color: var(--text);
}
.kpi {
  display:flex; gap:0.8rem; align-items:center; justify-content:space-between;
}
.kpi .val { font-size: 1.35rem; font-weight: 800; }
.kpi .lab { color: var(--muted); font-size: 0.92rem; }
.good { color: var(--good); }
.warn { color: var(--warn); }
.bad { color: var(--bad); }
a { color: var(--brand2) !important; }
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stSelectbox > div > div > div,
.stTextArea textarea {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
}
.stButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  background: rgba(122,162,255,0.18) !important;
  color: var(--text) !important;
  font-weight: 700 !important;
}
.stButton > button:hover { background: rgba(122,162,255,0.28) !important; }
div[data-testid="stSidebar"] {
  background: rgba(255,255,255,0.03);
  border-right: 1px solid rgba(255,255,255,0.08);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------
# Utilities
# -----------------------------
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def haversine_miles(lat1, lon1, lat2, lon2):
    # Miles
    R = 3958.7613
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def clamp(v, lo, hi): return max(lo, min(hi, v))

def safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def parse_money(s: str) -> Optional[float]:
    if s is None: return None
    m = re.findall(r"[-]?\$?\s*([0-9]+(?:\.[0-9]{1,2})?)", str(s))
    return float(m[0]) if m else None

def detect_doc_type(filename: str, text: str) -> str:
    name = (filename or "").lower()
    t = (text or "").lower()
    if "bol" in name or "bill of lading" in t: return "BOL"
    if "rate" in name or "rate con" in t or "rate confirmation" in t: return "RateCon"
    if "pod" in name or "proof of delivery" in t: return "POD"
    if "cdl" in name or "commercial driver" in t: return "CDL"
    if "med" in name or "medical" in t: return "MedCard"
    if "ifta" in name or "fuel tax" in t: return "IFTA"
    if "irp" in name: return "IRP"
    if "dvir" in name or "inspection" in t: return "DVIR"
    if "eld" in name or "hours of service" in t: return "ELD"
    return "Other"

def best_effort_text_from_upload(uploaded) -> Tuple[str, str]:
    """
    Returns (kind, text)
    kind: 'text' or 'binary'
    """
    if uploaded is None:
        return ("text", "")
    name = uploaded.name.lower()
    data = uploaded.getvalue()
    # Try decode as text
    try:
        txt = data.decode("utf-8", errors="ignore")
        if len(txt.strip()) > 0 and sum(c.isprintable() for c in txt[:2000]) > 500:
            return ("text", txt)
    except Exception:
        pass
    # Best effort: if it's a CSV, try parse & stringify
    if name.endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(data))
            return ("text", df.to_csv(index=False))
        except Exception:
            pass
    return ("binary", "")

def heuristic_extract_fields(doc_type: str, text: str) -> Dict[str, Any]:
    """
    LOCAL heuristic extraction from plain text.
    This is NOT legal/compliance advice; user should verify.
    """
    t = text or ""
    fields = {}

    # Common patterns
    # BOL / RateCon: shipper, consignee, pickup/delivery dates, address lines, PO, reference, weight, rate
    def find_first(patterns: List[str]):
        for p in patterns:
            m = re.search(p, t, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return None

    fields["doc_type"] = doc_type

    fields["load_id"] = find_first([
        r"Load\s*ID[:#]?\s*([A-Za-z0-9\-]+)",
        r"Reference[:#]?\s*([A-Za-z0-9\-]+)",
        r"Pro\s*No[:#]?\s*([A-Za-z0-9\-]+)",
        r"BOL\s*No[:#]?\s*([A-Za-z0-9\-]+)",
    ])

    fields["shipper"] = find_first([
        r"Shipper[:\s]+(.+)",
        r"From[:\s]+(.+)",
    ])
    fields["consignee"] = find_first([
        r"Consignee[:\s]+(.+)",
        r"To[:\s]+(.+)",
        r"Deliver\s*To[:\s]+(.+)"
    ])

    fields["pickup_date"] = find_first([
        r"Pickup\s*Date[:\s]+([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
        r"Pick\s*Up[:\s]+([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
    ])
    fields["delivery_date"] = find_first([
        r"Delivery\s*Date[:\s]+([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
        r"Deliver(?:y)?[:\s]+([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
    ])

    fields["pickup_city_state"] = find_first([
        r"Pickup\s*Location[:\s]+(.+)",
        r"Origin[:\s]+(.+)",
    ])
    fields["delivery_city_state"] = find_first([
        r"Delivery\s*Location[:\s]+(.+)",
        r"Destination[:\s]+(.+)",
    ])

    fields["commodity"] = find_first([
        r"Commodity[:\s]+(.+)",
        r"Description[:\s]+(.+)"
    ])
    fields["weight_lbs"] = safe_float(find_first([
        r"Weight[:\s]+([0-9,]+)\s*lbs",
        r"Gross\s*Weight[:\s]+([0-9,]+)",
    ]).replace(",", "") if find_first([r"Weight[:\s]+([0-9,]+)", r"Gross\s*Weight[:\s]+([0-9,]+)"]) else None, None)

    rate = find_first([
        r"Rate[:\s]+\$?([0-9,]+(?:\.[0-9]{1,2})?)",
        r"Total\s*Charges[:\s]+\$?([0-9,]+(?:\.[0-9]{1,2})?)",
    ])
    fields["rate_usd"] = float(rate.replace(",", "")) if rate else None

    # CDL / Med card
    fields["driver_name"] = find_first([
        r"Name[:\s]+(.+)",
        r"Driver[:\s]+(.+)"
    ])
    fields["license_number"] = find_first([
        r"License\s*(?:No\.|Number)?[:\s]+([A-Za-z0-9\-]+)"
    ])
    fields["exp_date"] = find_first([
        r"Exp(?:iration)?\s*Date[:\s]+([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
        r"Expires[:\s]+([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})"
    ])

    # ELD rough
    fields["carrier"] = find_first([r"Carrier[:\s]+(.+)", r"Company[:\s]+(.+)"])
    fields["dot"] = find_first([r"USDOT[:\s#]+([0-9]+)", r"DOT[:\s#]+([0-9]+)"])

    # Clean up empties
    return {k: v for k, v in fields.items() if v not in (None, "", "None")}

def pretty_kv(d: Dict[str, Any]) -> str:
    if not d: return ""
    lines = []
    for k, v in d.items():
        lines.append(f"**{k.replace('_',' ').title()}**: {v}")
    return "\n\n".join(lines)

def init_state():
    if "tier" not in st.session_state:
        st.session_state.tier = "Free"
    if "docs" not in st.session_state:
        st.session_state.docs = []  # list of dicts
    if "trips" not in st.session_state:
        st.session_state.trips = []  # list of dicts
    if "expenses" not in st.session_state:
        st.session_state.expenses = []  # list of dicts
    if "assets" not in st.session_state:
        st.session_state.assets = {
            "tractor": {"unit": "T-12", "plate": "", "vin": "", "height_ft": 13.6, "gross_lbs": 80000, "hazmat": False},
            "trailer": {"unit": "TR-7", "type": "Dry Van", "length_ft": 53}
        }
    if "alerts" not in st.session_state:
        st.session_state.alerts = []
    if "pro_unlock_code" not in st.session_state:
        st.session_state.pro_unlock_code = ""
    if "ui_mode" not in st.session_state:
        st.session_state.ui_mode = "Operator (Simple)"
    if "last_guardrail" not in st.session_state:
        st.session_state.last_guardrail = {}

init_state()

# -----------------------------
# Feature gating
# -----------------------------
PRO_FEATURES = {
    "Bulk Export (ZIP/CSV bundle)",
    "Multi-driver / Team profiles",
    "Automated Compliance Reminders",
    "IFTA by GPS (fine-grained)",
    "Smart Doc Matching (BOL↔RateCon↔POD)",
    "Audit-ready Report Pack",
}

def is_pro() -> bool:
    return st.session_state.tier == "Pro"

def gate(feature_name: str, help_text: str = "") -> bool:
    """Return True if allowed; otherwise render upgrade hint and return False."""
    if is_pro():
        return True
    st.info(f"🔒 **{feature_name}** is a Pro feature. {help_text}".strip())
    return False

# -----------------------------
# SIMULATED rules engine (legal pre-thinking)
# -----------------------------
SIM_STATE_RULES = {
    "IL": {"winter_restriction": False, "special_permit_note": "Oversize/overweight may require IL permits."},
    "IN": {"winter_restriction": False, "special_permit_note": "Watch toll roads; ELD compliance standard."},
    "WI": {"winter_restriction": True,  "special_permit_note": "Seasonal weight limits can apply (SIMULATED)."},
    "IA": {"winter_restriction": False, "special_permit_note": "General compliance; verify oversize permits."},
    "MO": {"winter_restriction": False, "special_permit_note": "Bridge/route restrictions vary by corridor."},
    "TX": {"winter_restriction": False, "special_permit_note": "Hazmat routing restrictions in metros (SIMULATED)."},
}

# Super simplified “state bounding boxes” (NOT accurate enough for compliance; used for demo IFTA splits)
SIM_STATE_BBOX = {
    "IL": (36.98, -91.51, 42.51, -87.02),
    "IN": (37.77, -88.10, 41.77, -84.78),
    "WI": (42.49, -92.89, 47.31, -86.76),
    "IA": (40.38, -96.64, 43.50, -90.14),
    "MO": (35.99, -95.77, 40.61, -89.10),
    "TX": (25.84, -106.65, 36.50, -93.51),
}

def guess_state(lat: float, lon: float) -> str:
    for s, (lat_min, lon_min, lat_max, lon_max) in SIM_STATE_BBOX.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return s
    return "UNK"

def simulate_truck_safe_checks(origin: Tuple[float,float], dest: Tuple[float,float], vehicle: Dict[str, Any]) -> Dict[str, Any]:
    """
    SIMULATED: returns guardrail result including bridge clearance risk and general notes.
    """
    lat1, lon1 = origin
    lat2, lon2 = dest
    dist = haversine_miles(lat1, lon1, lat2, lon2)
    # fake "minimum bridge height along route" based on distance + randomness seeded by coords
    seed = int((abs(lat1*1000)+abs(lon1*1000)+abs(lat2*1000)+abs(lon2*1000)) * 10) % 997
    rng = np.random.default_rng(seed)
    simulated_min_bridge_ft = float(np.round(rng.uniform(11.8, 15.2), 1))

    height_ft = float(vehicle.get("height_ft", 13.6))
    clearance_margin_ft = simulated_min_bridge_ft - height_ft

    risk = "OK"
    if clearance_margin_ft < 0.5:
        risk = "HIGH"
    elif clearance_margin_ft < 1.0:
        risk = "MED"

    hazmat = bool(vehicle.get("hazmat", False))
    origin_state = guess_state(lat1, lon1)
    dest_state = guess_state(lat2, lon2)

    notes = []
    notes.append("SIMULATED analysis — verify with official routing/permit sources.")
    if hazmat:
        notes.append("Hazmat flagged — metro restrictions may apply (SIMULATED).")
    if origin_state in SIM_STATE_RULES:
        notes.append(f"{origin_state}: {SIM_STATE_RULES[origin_state]['special_permit_note']}")
    if dest_state in SIM_STATE_RULES:
        notes.append(f"{dest_state}: {SIM_STATE_RULES[dest_state]['special_permit_note']}")

    return {
        "distance_mi_est": round(dist, 1),
        "min_bridge_height_ft_sim": simulated_min_bridge_ft,
        "vehicle_height_ft": height_ft,
        "clearance_margin_ft_sim": round(clearance_margin_ft, 1),
        "risk": risk,
        "origin_state_sim": origin_state,
        "dest_state_sim": dest_state,
        "notes": notes,
        "timestamp": now_ts(),
    }

def simulate_ifta_split(origin: Tuple[float,float], dest: Tuple[float,float]) -> Dict[str, float]:
    """
    SIMULATED IFTA split by coarse state bounding boxes.
    - Uses straight line interpolation.
    - Not accurate enough for filing; demo only.
    """
    lat1, lon1 = origin
    lat2, lon2 = dest
    total = haversine_miles(lat1, lon1, lat2, lon2)
    if total <= 0.5:
        s = guess_state(lat1, lon1)
        return {s: round(total, 1)}

    points = 60
    miles_per_seg = total / (points - 1)
    agg = {}
    for i in range(points):
        a = i/(points-1)
        lat = lat1*(1-a) + lat2*a
        lon = lon1*(1-a) + lon2*a
        s = guess_state(lat, lon)
        agg[s] = agg.get(s, 0.0) + miles_per_seg
    return {k: round(v, 1) for k, v in agg.items() if v > 0.05}

# -----------------------------
# Sidebar: tier + navigation
# -----------------------------
with st.sidebar:
    st.markdown('<div class="h1">🛻 RollSafe</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Dispatch + Compliance OS (free-stack prototype)</div>', unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    # UI mode
    st.session_state.ui_mode = st.selectbox(
        "UI Mode",
        ["Operator (Simple)", "Power User (Dense)"],
        index=0 if st.session_state.ui_mode == "Operator (Simple)" else 1
    )

    # Tier switch (demo)
    c1, c2 = st.columns([1,1])
    with c1:
        st.markdown(f'<div class="badge">Tier: <b>{st.session_state.tier}</b></div>', unsafe_allow_html=True)
    with c2:
        if st.button("Toggle Pro (Demo)"):
            st.session_state.tier = "Pro" if st.session_state.tier == "Free" else "Free"

    st.caption("Free users get full core workflow. Pro gates automation + audit packs (demo).")

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    nav = st.radio(
        "Navigate",
        ["Command Center", "Digital Folder", "Trip Planner", "Compliance Monitor", "IFTA + Costs", "Subscription Billing", "Settings"],
        index=0
    )

# -----------------------------
# Top header
# -----------------------------
st.markdown(
    f"""
<div class="card2">
  <div class="kpi">
    <div>
      <div class="h1">Command-ready workflow</div>
      <div class="small-muted">Local-first docs • Simple trip planning • Compliance tracking • SIMULATED legal pre-thinking</div>
    </div>
    <div style="text-align:right">
      <span class="badge">Local-first</span>
      <span class="badge">No paid APIs</span>
      <span class="badge">Last update: {now_ts()}</span>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# -----------------------------
# Data helpers (seed defaults)
# -----------------------------
def seed_demo_data_if_empty():
    if len(st.session_state.trips) == 0:
        st.session_state.trips.append({
            "trip_id": "TRIP-1001",
            "created": now_ts(),
            "load_id": "LD-7781",
            "origin_name": "Chicago, IL (SIM)",
            "origin_lat": 41.8781, "origin_lon": -87.6298,
            "dest_name": "Indianapolis, IN (SIM)",
            "dest_lat": 39.7684, "dest_lon": -86.1581,
            "status": "Planned",
            "driver": "Unassigned",
            "truck": st.session_state.assets["tractor"]["unit"],
            "hazmat": False,
        })
    if len(st.session_state.expenses) == 0:
        st.session_state.expenses.extend([
            {"date": str(date.today() - timedelta(days=3)), "type": "Fuel", "vendor": "Pilot (SIM)", "amount": 412.77, "notes": "Diesel", "trip_id": "TRIP-1001", "state_sim": "IL"},
            {"date": str(date.today() - timedelta(days=2)), "type": "Toll", "vendor": "Tollway (SIM)", "amount": 23.50, "notes": "", "trip_id": "TRIP-1001", "state_sim": "IN"},
        ])

seed_demo_data_if_empty()

# -----------------------------
# Widgets: guardrail + alerts
# -----------------------------
def render_guardrail(guard: Dict[str, Any]):
    if not guard:
        st.markdown('<div class="card"><div class="h2">🛡️ Legal Safety Guardrail</div><div class="small-muted">Plan a trip to see guardrail output.</div></div>', unsafe_allow_html=True)
        return

    risk = guard.get("risk", "OK")
    color_class = "good" if risk == "OK" else ("warn" if risk == "MED" else "bad")
    risk_label = "OK" if risk == "OK" else ("MED RISK" if risk == "MED" else "HIGH RISK")

    st.markdown(
        f"""
<div class="card">
  <div class="h2">🛡️ Legal Safety Guardrail</div>
  <div class="small-muted">SIMULATED checks. Always verify using official routing/permit sources.</div>
  <div class="hr"></div>
  <div class="kpi">
    <div>
      <div class="lab">Risk</div>
      <div class="val {color_class}">{risk_label}</div>
    </div>
    <div>
      <div class="lab">Distance (est)</div>
      <div class="val">{guard.get("distance_mi_est","—")} mi</div>
    </div>
    <div>
      <div class="lab">Min bridge (SIM)</div>
      <div class="val">{guard.get("min_bridge_height_ft_sim","—")} ft</div>
    </div>
    <div>
      <div class="lab">Clearance margin (SIM)</div>
      <div class="val">{guard.get("clearance_margin_ft_sim","—")} ft</div>
    </div>
  </div>
  <div class="hr"></div>
  <div class="small-muted">
    <ul>
      {''.join([f"<li>{st._utils.escape_markdown(n)}</li>" for n in guard.get("notes", [])])}
    </ul>
  </div>
</div>
""",
        unsafe_allow_html=True
    )

def add_alert(kind: str, msg: str, severity: str = "info"):
    st.session_state.alerts.append({
        "ts": now_ts(), "kind": kind, "msg": msg, "severity": severity
    })

def render_alerts_compact():
    if not st.session_state.alerts:
        return
    # last 5
    recent = st.session_state.alerts[-5:][::-1]
    st.markdown('<div class="card"><div class="h2">🔔 Alerts</div>', unsafe_allow_html=True)
    for a in recent:
        sev = a["severity"]
        icon = "✅" if sev == "good" else ("⚠️" if sev == "warn" else ("🛑" if sev == "bad" else "ℹ️"))
        st.markdown(f"- {icon} **{a['kind']}** — {a['msg']}  \n  <span class='small-muted'>{a['ts']}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Page: Command Center
# -----------------------------
if nav == "Command Center":
    left, right = st.columns([1.2, 0.8], gap="large")

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="h2">📊 Command Center</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">Today’s view: trips, compliance, and cash flow.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        trips_df = pd.DataFrame(st.session_state.trips)
        exp_df = pd.DataFrame(st.session_state.expenses)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='kpi'><div><div class='lab'>Trips</div><div class='val'>{len(trips_df)}</div></div></div>", unsafe_allow_html=True)
        with c2:
            planned = int((trips_df["status"] == "Planned").sum()) if len(trips_df) else 0
            st.markdown(f"<div class='kpi'><div><div class='lab'>Planned</div><div class='val'>{planned}</div></div></div>", unsafe_allow_html=True)
        with c3:
            spend_30 = float(exp_df[pd.to_datetime(exp_df["date"]) >= (pd.Timestamp.today() - pd.Timedelta(days=30))]["amount"].sum()) if len(exp_df) else 0.0
            st.markdown(f"<div class='kpi'><div><div class='lab'>Spend (30d)</div><div class='val'>${spend_30:,.0f}</div></div></div>", unsafe_allow_html=True)
        with c4:
            docs_count = len(st.session_state.docs)
            st.markdown(f"<div class='kpi'><div><div class='lab'>Docs</div><div class='val'>{docs_count}</div></div></div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("**Recent trips**")
        if len(trips_df):
            show_cols = ["trip_id", "load_id", "origin_name", "dest_name", "status", "driver", "truck"]
            st.dataframe(trips_df[show_cols].tail(8), use_container_width=True, hide_index=True)
        else:
            st.info("No trips yet. Create one in Trip Planner.")

        st.write("")
        st.markdown("**Spend trend**")
        if len(exp_df):
            exp_df2 = exp_df.copy()
            exp_df2["date"] = pd.to_datetime(exp_df2["date"])
            chart = (
                alt.Chart(exp_df2)
                .mark_area(opacity=0.35, color="#7aa2ff")
                .encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("amount:Q", title="Amount ($)"),
                    tooltip=["date:T", "type:N", "vendor:N", "amount:Q"]
                )
                .properties(height=220)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("No expenses recorded yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        render_guardrail(st.session_state.last_guardrail)
        st.write("")
        render_alerts_compact()

# -----------------------------
# Page: Digital Folder
# -----------------------------
elif nav == "Digital Folder":
    colA, colB = st.columns([1.1, 0.9], gap="large")

    with colA:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="h2">📁 Digital Folder</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">Drop documents. We’ll auto-detect type + extract fields (local, best-effort).</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload BOL / RateCon / POD / CDL / Med Card / IFTA / IRP / DVIR / ELD exports",
            type=None,
            accept_multiple_files=True
        )

        colU1, colU2 = st.columns([0.65, 0.35])
        with colU1:
            privacy_mode = st.selectbox(
                "Privacy Mode",
                ["Local-only (recommended)", "Local + optional external (DISABLED in this prototype)"],
                index=0
            )
        with colU2:
            auto_link = st.toggle("Auto-link docs to trips (SIM)", value=True)

        if uploaded:
            for f in uploaded:
                kind, text = best_effort_text_from_upload(f)
                doc_type = detect_doc_type(f.name, text)
                extracted = heuristic_extract_fields(doc_type, text) if kind == "text" else {"doc_type": doc_type, "note": "Binary file uploaded. OCR not enabled in this free prototype."}

                doc_id = f"DOC-{len(st.session_state.docs)+1000}"
                rec = {
                    "doc_id": doc_id,
                    "filename": f.name,
                    "uploaded": now_ts(),
                    "doc_type": doc_type,
                    "size_kb": round(len(f.getvalue())/1024, 1),
                    "extracted": extracted,
                    "raw_text_preview": (text[:1200] + ("..." if len(text) > 1200 else "")) if kind == "text" else "",
                    "linked_trip_id": None
                }

                # SIM auto-link: if extracted has load_id, match to trip load_id
                if auto_link and kind == "text":
                    lid = extracted.get("load_id")
                    if lid:
                        for tr in st.session_state.trips:
                            if str(tr.get("load_id","")).strip() == str(lid).strip():
                                rec["linked_trip_id"] = tr["trip_id"]
                                add_alert("Doc Linked", f"{f.name} linked to {tr['trip_id']} (SIM)", "good")
                                break

                st.session_state.docs.append(rec)
            add_alert("Upload", f"Uploaded {len(uploaded)} file(s).", "good")
            st.success("Uploaded and indexed.")

        st.write("")
        docs_df = pd.DataFrame([{
            "doc_id": d["doc_id"],
            "filename": d["filename"],
            "type": d["doc_type"],
            "size_kb": d["size_kb"],
            "uploaded": d["uploaded"],
            "linked_trip_id": d.get("linked_trip_id") or ""
        } for d in st.session_state.docs])

        st.markdown("**Folder index**")
        if len(docs_df):
            st.dataframe(docs_df.sort_values("uploaded", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No documents yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="h2">🔎 Doc Viewer + Extraction</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">Pick a document to review extracted fields.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        if st.session_state.docs:
            pick = st.selectbox("Select a document", [d["doc_id"] + " — " + d["filename"] for d in st.session_state.docs][::-1])
            doc_id = pick.split(" — ")[0]
            doc = next(d for d in st.session_state.docs if d["doc_id"] == doc_id)

            st.markdown(f"**Type:** {doc['doc_type']}  \n**Uploaded:** {doc['uploaded']}  \n**Linked Trip:** {doc.get('linked_trip_id') or '—'}")
            st.write("")
            st.markdown("**Extracted fields (best-effort)**")
            st.markdown(pretty_kv(doc.get("extracted", {})) or "_No fields extracted._")

            if doc.get("raw_text_preview"):
                with st.expander("Raw text preview"):
                    st.code(doc["raw_text_preview"])

            st.write("")
            if gate("Smart Doc Matching (BOL↔RateCon↔POD)", "Auto-match by entities + signatures."):
                st.button("Run Smart Matching", disabled=not is_pro())
        else:
            st.caption("Upload a doc to view it here.")

        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Page: Trip Planner
# -----------------------------
elif nav == "Trip Planner":
    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="h2">🗺️ Trip Planner</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">Free trip planning with map + SIMULATED truck-safe checks.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # Inputs
        c1, c2, c3 = st.columns([0.34, 0.33, 0.33])
        with c1:
            trip_id = st.text_input("Trip ID", value=f"TRIP-{1000 + len(st.session_state.trips) + 1}")
            load_id = st.text_input("Load ID", value=f"LD-{7000 + len(st.session_state.trips) + 1}")
        with c2:
            driver = st.text_input("Driver", value="Unassigned")
            truck_unit = st.text_input("Truck Unit", value=st.session_state.assets["tractor"]["unit"])
        with c3:
            status = st.selectbox("Status", ["Planned", "In Transit", "Delivered"], index=0)
            hazmat = st.toggle("Hazmat?", value=st.session_state.assets["tractor"]["hazmat"])

        st.markdown("**Origin (lat/lon)**")
        o1, o2, o3 = st.columns([0.55, 0.23, 0.22])
        with o1:
            origin_name = st.text_input("Origin name", value="Chicago, IL (SIM)")
        with o2:
            o_lat = st.number_input("Origin lat", value=41.8781, format="%.5f")
        with o3:
            o_lon = st.number_input("Origin lon", value=-87.6298, format="%.5f")

        st.markdown("**Destination (lat/lon)**")
        d1, d2, d3 = st.columns([0.55, 0.23, 0.22])
        with d1:
            dest_name = st.text_input("Destination name", value="Indianapolis, IN (SIM)")
        with d2:
            d_lat = st.number_input("Dest lat", value=39.7684, format="%.5f")
        with d3:
            d_lon = st.number_input("Dest lon", value=-86.1581, format="%.5f")

        st.write("")
        plan_btn, save_btn = st.columns([0.33, 0.67])
        with plan_btn:
            if st.button("Run Guardrail Check"):
                st.session_state.assets["tractor"]["hazmat"] = hazmat
                guard = simulate_truck_safe_checks((o_lat, o_lon), (d_lat, d_lon), st.session_state.assets["tractor"])
                st.session_state.last_guardrail = guard
                sev = "good" if guard["risk"] == "OK" else ("warn" if guard["risk"] == "MED" else "bad")
                add_alert("Guardrail", f"{guard['risk']} risk — clearance margin {guard['clearance_margin_ft_sim']} ft (SIM)", sev)
        with save_btn:
            if st.button("Save Trip"):
                trip = {
                    "trip_id": trip_id.strip(),
                    "created": now_ts(),
                    "load_id": load_id.strip(),
                    "origin_name": origin_name, "origin_lat": float(o_lat), "origin_lon": float(o_lon),
                    "dest_name": dest_name, "dest_lat": float(d_lat), "dest_lon": float(d_lon),
                    "status": status,
                    "driver": driver.strip() or "Unassigned",
                    "truck": truck_unit.strip() or st.session_state.assets["tractor"]["unit"],
                    "hazmat": bool(hazmat),
                }
                st.session_state.trips.append(trip)
                add_alert("Trip Saved", f"{trip['trip_id']} ({status})", "good")
                st.success("Trip saved.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        # Map + route line
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="h2">🧭 Map</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">Uses OpenStreetMap tiles (free). Route line is straight-line (SIM).</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        center_lat = (o_lat + d_lat) / 2
        center_lon = (o_lon + d_lon) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="OpenStreetMap")
        folium.Marker([o_lat, o_lon], popup="Origin", tooltip="Origin", icon=folium.Icon(color="blue", icon="play")).add_to(m)
        folium.Marker([d_lat, d_lon], popup="Destination", tooltip="Destination", icon=folium.Icon(color="red", icon="flag")).add_to(m)
        folium.PolyLine([[o_lat, o_lon], [d_lat, d_lon]], color="#7aa2ff", weight=5, opacity=0.85).add_to(m)

        _ = st_folium(m, height=430, use_container_width=True)

        st.write("")
        render_guardrail(st.session_state.last_guardrail)

        st.write("")
        st.markdown('<div class="card2">', unsafe_allow_html=True)
        st.markdown("**IFTA Split (SIMULATED)**")
        split = simulate_ifta_split((o_lat, o_lon), (d_lat, d_lon))
        ifta_df = pd.DataFrame([{"state_sim": k, "miles_sim": v} for k, v in split.items()]).sort_values("miles_sim", ascending=False)
        st.dataframe(ifta_df, use_container_width=True, hide_index=True)
        st.caption("Not accurate enough for filing. Demo only.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Page: Compliance Monitor
# -----------------------------
elif nav == "Compliance Monitor":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="h2">✅ Compliance Monitor</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Track expirations, docs, and reminders. No legal advice — you must verify requirements.</div>', unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    # Simple compliance items
    default_items = [
        {"item": "CDL", "owner": "Driver", "exp": date.today() + timedelta(days=120), "status": "OK"},
        {"item": "Medical Card", "owner": "Driver", "exp": date.today() + timedelta(days=45), "status": "DUE SOON"},
        {"item": "Annual Inspection", "owner": "Truck", "exp": date.today() + timedelta(days=12), "status": "DUE SOON"},
        {"item": "IFTA Filing", "owner": "Carrier", "exp": date.today() + timedelta(days=18), "status": "DUE SOON"},
        {"item": "IRP Renewal", "owner": "Carrier", "exp": date.today() + timedelta(days=210), "status": "OK"},
    ]
    df = pd.DataFrame(default_items)
    df["days_left"] = (pd.to_datetime(df["exp"]) - pd.Timestamp.today().normalize()).dt.days

    def status_color(s):
        if s == "OK": return "good"
        if "SOON" in s: return "warn"
        return "bad"

    c1, c2, c3 = st.columns([0.45, 0.35, 0.20])
    with c1:
        st.markdown("**At-a-glance**")
        due_soon = int((df["days_left"] <= 45).sum())
        st.markdown(f"- Items due within 45 days: **{due_soon}**")
        st.markdown(f"- Total tracked: **{len(df)}**")
    with c2:
        st.markdown("**Upload shortcuts**")
        st.caption("Tip: upload CDL/MedCard/PODs in Digital Folder to keep audits clean.")
        st.button("Go to Digital Folder", on_click=lambda: None)
    with c3:
        if gate("Automated Compliance Reminders", "Email/SMS + calendar sync in Pro."):
            st.button("Enable reminders", disabled=not is_pro())

    st.write("")
    st.markdown("**Compliance table**")
    st.dataframe(df[["item","owner","exp","days_left","status"]].sort_values("days_left"), use_container_width=True, hide_index=True)

    st.write("")
    st.markdown("**Quick risk notes (SIMULATED)**")
    st.caption("These are generic pointers. Verify state and federal rules with official sources.")
    st.markdown("- Hazmat shipments: metro routing restrictions can apply (SIMULATED).")
    st.markdown("- Height/weight: permits required above limits; bridge clearance must be verified (SIMULATED).")
    st.markdown("- Recordkeeping: keep BOL/RateCon/POD linked to the trip for audit hygiene.")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Page: IFTA + Costs
# -----------------------------
elif nav == "IFTA + Costs":
    top, bottom = st.columns([1, 1], gap="large")

    with top:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="h2">⛽ IFTA + Costs</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">Track expenses and produce simple IFTA mileage summaries (SIMULATED).</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        trips = st.session_state.trips
        trip_ids = [t["trip_id"] for t in trips] if trips else []
        col1, col2, col3, col4 = st.columns([0.22, 0.22, 0.28, 0.28])
        with col1:
            exp_date = st.date_input("Date", value=date.today())
        with col2:
            exp_type = st.selectbox("Type", ["Fuel", "Toll", "Repair", "Parking", "Scale", "Other"], index=0)
        with col3:
            vendor = st.text_input("Vendor", value="")
        with col4:
            amount = st.number_input("Amount ($)", min_value=0.0, value=0.0, step=1.0)

        col5, col6 = st.columns([0.55, 0.45])
        with col5:
            notes = st.text_input("Notes", value="")
        with col6:
            trip_pick = st.selectbox("Trip", ["(unassigned)"] + trip_ids, index=0)

        if st.button("Add expense"):
            rec = {
                "date": str(exp_date),
                "type": exp_type,
                "vendor": vendor or "(unknown)",
                "amount": float(amount),
                "notes": notes,
                "trip_id": "" if trip_pick == "(unassigned)" else trip_pick,
                "state_sim": "UNK"
            }
            st.session_state.expenses.append(rec)
            add_alert("Expense", f"{exp_type} ${amount:,.2f} ({vendor or 'vendor'})", "good")
            st.success("Expense added.")

        st.markdown("</div>", unsafe_allow_html=True)

    with bottom:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="h2">📈 Analytics</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">Basic cost tracking. Pro adds audit pack exports.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        exp_df = pd.DataFrame(st.session_state.expenses)
        if len(exp_df):
            exp_df["date"] = pd.to_datetime(exp_df["date"])
            exp_df["month"] = exp_df["date"].dt.to_period("M").astype(str)

            by_type = exp_df.groupby("type", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            chart1 = (
                alt.Chart(by_type)
                .mark_bar(color="#9bf6ff")
                .encode(
                    x=alt.X("amount:Q", title="Amount ($)"),
                    y=alt.Y("type:N", sort="-x", title=""),
                    tooltip=["type:N","amount:Q"]
                )
                .properties(height=260)
            )
            st.altair_chart(chart1, use_container_width=True)

            st.write("")
            st.markdown("**Expense ledger**")
            st.dataframe(exp_df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No expenses recorded yet.")

        st.write("")
        st.markdown("**IFTA quarterly summary (SIMULATED)**")
        if gate("IFTA by GPS (fine-grained)", "This prototype uses coarse bounding boxes + straight-line splits."):
            st.caption("Pro would support GPS logs and accurate state splits.")
        # Free: show simplified summary based on saved trips
        rows = []
        for t in st.session_state.trips:
            split = simulate_ifta_split((t["origin_lat"], t["origin_lon"]), (t["dest_lat"], t["dest_lon"]))
            for s, miles in split.items():
                rows.append({"trip_id": t["trip_id"], "state_sim": s, "miles_sim": miles})
        if rows:
            s_df = pd.DataFrame(rows)
            s_sum = s_df.groupby("state_sim", as_index=False)["miles_sim"].sum().sort_values("miles_sim", ascending=False)
            st.dataframe(s_sum, use_container_width=True, hide_index=True)
            st.caption("Demo only — not filing-grade.")
        else:
            st.caption("Create trips to generate IFTA splits.")

        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Page: Subscription Billing
# -----------------------------
elif nav == "Subscription Billing":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="h2">💳 Subscription Billing (Demo)</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">This prototype shows feature gating. Real billing can be added later (Stripe).</div>', unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([0.55, 0.45], gap="large")
    with c1:
        st.markdown("**Current tier**")
        st.markdown(f"- Tier: **{st.session_state.tier}**")
        st.markdown("- Billing: **Disabled in prototype** (no external calls).")
        st.write("")
        st.markdown("**Included in Free**")
        st.markdown("- Digital Folder uploads + basic extraction (local best-effort)")
        st.markdown("- Trip Planner + map + SIM guardrail checks")
        st.markdown("- Compliance table + manual tracking")
        st.markdown("- Expenses ledger + basic analytics")
        st.write("")
        st.markdown("**Pro adds (demo-gated)**")
        for f in sorted(PRO_FEATURES):
            st.markdown(f"- 🔒 {f}")

    with c2:
        st.markdown("**Upgrade controls (demo only)**")
        st.caption("In production: Stripe Customer Portal + webhooks.")
        if st.button("Switch to Free"):
            st.session_state.tier = "Free"
            add_alert("Tier", "Switched to Free (demo).", "info")
        if st.button("Switch to Pro"):
            st.session_state.tier = "Pro"
            add_alert("Tier", "Switched to Pro (demo).", "good")

        st.write("")
        if gate("Audit-ready Report Pack", "Generate a zipped audit binder: docs + trip ledger + compliance log."):
            st.button("Generate Audit Pack", disabled=not is_pro())

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Page: Settings
# -----------------------------
elif nav == "Settings":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="h2">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Configure vehicle profile and risk posture. This is not legal advice.</div>', unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([0.55, 0.45], gap="large")
    with c1:
        st.markdown("**Vehicle profile**")
        tractor = st.session_state.assets["tractor"]
        tractor["unit"] = st.text_input("Tractor unit", value=tractor.get("unit","T-12"))
        tractor["height_ft"] = st.number_input("Vehicle height (ft)", min_value=10.0, max_value=16.5, value=float(tractor.get("height_ft", 13.6)), step=0.1)
        tractor["gross_lbs"] = st.number_input("Gross weight (lbs)", min_value=10000, max_value=200000, value=int(tractor.get("gross_lbs", 80000)), step=1000)
        tractor["hazmat"] = st.toggle("Hazmat default", value=bool(tractor.get("hazmat", False)))
        st.session_state.assets["tractor"] = tractor

        trailer = st.session_state.assets["trailer"]
        trailer["unit"] = st.text_input("Trailer unit", value=trailer.get("unit","TR-7"))
        trailer["type"] = st.selectbox("Trailer type", ["Dry Van", "Reefer", "Flatbed", "Tanker"], index=["Dry Van","Reefer","Flatbed","Tanker"].index(trailer.get("type","Dry Van")))
        trailer["length_ft"] = st.number_input("Trailer length (ft)", min_value=20, max_value=60, value=int(trailer.get("length_ft", 53)), step=1)
        st.session_state.assets["trailer"] = trailer

        st.write("")
        if st.button("Save settings"):
            add_alert("Settings", "Vehicle profile updated.", "good")
            st.success("Saved.")

    with c2:
        st.markdown("**Legal posture (recommended)**")
        st.markdown(
            """
- Keep guardrail outputs labeled **SIMULATED** until you integrate a verified data provider.
- For IFTA, use **GPS logs** + verified state boundaries when filing.
- For OCR, avoid transmitting documents to third parties unless you have **clear consent + retention policy**.
            """
        )
        st.write("")
        st.markdown("**Data controls**")
        if st.button("Clear alerts"):
            st.session_state.alerts = []
            st.success("Cleared.")
        if st.button("Clear docs"):
            st.session_state.docs = []
            st.success("Cleared.")
        if st.button("Clear trips + expenses"):
            st.session_state.trips = []
            st.session_state.expenses = []
            st.success("Cleared.")

        st.write("")
        st.markdown("**Exports (Free)**")
        trips_df = pd.DataFrame(st.session_state.trips)
        exp_df = pd.DataFrame(st.session_state.expenses)
        docs_df = pd.DataFrame([{
            "doc_id": d["doc_id"], "filename": d["filename"], "doc_type": d["doc_type"], "uploaded": d["uploaded"], "linked_trip_id": d.get("linked_trip_id","")
        } for d in st.session_state.docs])

        export = {
            "exported_at": now_ts(),
            "tier": st.session_state.tier,
            "trips": st.session_state.trips,
            "expenses": st.session_state.expenses,
            "docs_index": docs_df.to_dict(orient="records"),
            "note": "Docs raw file bytes not exported in this prototype."
        }
        st.download_button(
            "Download JSON snapshot",
            data=json.dumps(export, indent=2).encode("utf-8"),
            file_name=f"rollsafe_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.write("")
st.caption("⚠️ This is a prototype. All compliance/bridge/route checks and IFTA splits are SIMULATED and not legal advice.")
