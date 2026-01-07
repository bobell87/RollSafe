# app.py
# Elite Trucking Dashboard Prototype (Single-file Streamlit)
# Run: streamlit run app.py -> http://localhost:8501
# NOTE: This is a local prototype. OCR + routing are simulated/mocked by design.

import os
import re
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import streamlit as st
import pydeck as pdk

APP_TITLE = "Elite Trucker Dashboard (Prototype)"
UPLOAD_DIR = "uploads"  # local folder for prototype storage (replace with S3 later)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# Mock data + rules
# -----------------------------

# Mock "truck-safe" route graph: states traversed between sample cities
CITY_DB = {
    "Chicago, IL": {"lat": 41.8781, "lon": -87.6298, "state": "IL"},
    "Indianapolis, IN": {"lat": 39.7684, "lon": -86.1581, "state": "IN"},
    "St. Louis, MO": {"lat": 38.6270, "lon": -90.1994, "state": "MO"},
    "Nashville, TN": {"lat": 36.1627, "lon": -86.7816, "state": "TN"},
    "Atlanta, GA": {"lat": 33.7490, "lon": -84.3880, "state": "GA"},
    "Dallas, TX": {"lat": 32.7767, "lon": -96.7970, "state": "TX"},
    "Denver, CO": {"lat": 39.7392, "lon": -104.9903, "state": "CO"},
    "Phoenix, AZ": {"lat": 33.4484, "lon": -112.0740, "state": "AZ"},
    "Los Angeles, CA": {"lat": 34.0522, "lon": -118.2437, "state": "CA"},
}

# Mock state compliance rules (SIMULATED)
STATE_RULES = {
    "IL": {"max_gvw_lbs": 80000, "hazmat_restrictions": ["tunnel_ban"], "min_bridge_ft": 13.6},
    "IN": {"max_gvw_lbs": 80000, "hazmat_restrictions": [], "min_bridge_ft": 13.9},
    "MO": {"max_gvw_lbs": 80000, "hazmat_restrictions": [], "min_bridge_ft": 13.5},
    "TN": {"max_gvw_lbs": 80000, "hazmat_restrictions": ["city_center_ban"], "min_bridge_ft": 13.6},
    "GA": {"max_gvw_lbs": 80000, "hazmat_restrictions": [], "min_bridge_ft": 14.0},
    "TX": {"max_gvw_lbs": 80000, "hazmat_restrictions": [], "min_bridge_ft": 13.7},
    "CO": {"max_gvw_lbs": 80000, "hazmat_restrictions": ["mountain_pass_advisory"], "min_bridge_ft": 13.8},
    "AZ": {"max_gvw_lbs": 80000, "hazmat_restrictions": [], "min_bridge_ft": 13.6},
    "CA": {"max_gvw_lbs": 80000, "hazmat_restrictions": ["carb_compliance"], "min_bridge_ft": 14.0},
}

# Documents expected for "inspection mode"
INSPECTION_REQUIRED_DOCS = [
    ("CDL", "Driver License"),
    ("MEDCARD", "Medical Card"),
    ("REG", "Registration"),
    ("INS", "Insurance"),
    ("ELD", "ELD Logs / Summary"),
    ("BOL", "Bill of Lading (current load)"),
]

DOC_CATEGORIES = [
    "CDL",
    "MEDCARD",
    "REG",
    "INS",
    "ELD",
    "BOL",
    "IFTA",
    "IRP",
    "PERMIT",
    "MAINT",
    "OTHER",
]

TIER_FREE = "Free"
TIER_PRO = "Pro"

PRO_FEATURES = {
    "auto_ocr": True,
    "compliance_alerts": True,
    "inspection_mode": True,
    "trip_planner_advanced": True,
}
FREE_FEATURES = {
    "auto_ocr": False,
    "compliance_alerts": True,   # keep basic alerts in free
    "inspection_mode": False,
    "trip_planner_advanced": False,
}

# -----------------------------
# Utilities
# -----------------------------

def now_dt() -> datetime:
    return datetime.now()

def fmt_date(d: Optional[date]) -> str:
    return d.isoformat() if d else "—"

def load_bytes_to_disk(file) -> str:
    """Persist uploaded file to disk and return path (prototype only)."""
    file_id = str(uuid.uuid4())
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", file.name)
    path = os.path.join(UPLOAD_DIR, f"{file_id}__{safe_name}")
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return path

def guess_category(filename: str) -> str:
    name = filename.upper()
    if "CDL" in name or "LICENSE" in name:
        return "CDL"
    if "MED" in name or "CARD" in name:
        return "MEDCARD"
    if "REG" in name:
        return "REG"
    if "INS" in name or "POLICY" in name:
        return "INS"
    if "ELD" in name or "HOS" in name:
        return "ELD"
    if "BOL" in name or "BILL" in name or "LADING" in name:
        return "BOL"
    if "IFTA" in name:
        return "IFTA"
    if "IRP" in name:
        return "IRP"
    if "PERMIT" in name:
        return "PERMIT"
    if "MAINT" in name or "PM" in name or "SERVICE" in name:
        return "MAINT"
    return "OTHER"

def simulate_ocr_extract(file_name: str, category: str) -> Dict[str, Any]:
    """
    Simulated OCR extraction. Replace with real OCR pipeline later.
    This returns plausible fields + an expiry date for compliance monitoring.
    """
    base = os.path.basename(file_name)
    # Try to pick up an expiry pattern like exp_2026-05-10 from filename
    m = re.search(r"(?:EXP|EXPIRES|EXPIRY|EXPDATE)[-_ ]?(\d{4}-\d{2}-\d{2})", base.upper())
    expiry = None
    if m:
        try:
            expiry = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except Exception:
            expiry = None
    if not expiry:
        # Default expiries by category
        horizon_days = {
            "CDL": 365 * 2,
            "MEDCARD": 365,
            "REG": 365,
            "INS": 365,
            "ELD": 30,
            "BOL": 7,
        }.get(category, 180)
        expiry = (now_dt() + timedelta(days=horizon_days)).date()

    extracted = {
        "_extraction_mode": "SIMULATED_OCR",
        "doc_category": category,
        "doc_id": str(uuid.uuid4())[:8],
        "holder_or_company": "ACME Trucking LLC",
        "expiry_date": expiry.isoformat(),
        "confidence": round(0.72 + (hash(base) % 20) / 100, 2),  # 0.72-0.91
        "notes": "Replace simulate_ocr_extract() with real OCR + parsing (Textract/Vision/Tesseract).",
    }
    # Add some category-specific hints
    if category == "CDL":
        extracted.update({"license_state": "IL", "class": "A"})
    elif category == "MEDCARD":
        extracted.update({"medical_examiner": "Dr. Example"})
    elif category == "BOL":
        extracted.update({"shipper": "Example Shipper", "consignee": "Example Receiver"})
    return extracted

def parse_expiry(extracted: Dict[str, Any]) -> Optional[date]:
    s = extracted.get("expiry_date")
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def tier_features(tier: str) -> Dict[str, bool]:
    return PRO_FEATURES if tier == TIER_PRO else FREE_FEATURES

def build_mock_route(origin: str, dest: str) -> Dict[str, Any]:
    """
    Mock route builder: returns list of points and states traversed.
    Replace with real GPS routing API later.
    """
    o = CITY_DB[origin]
    d = CITY_DB[dest]
    # naive midpoint to draw a line; this is a *visual mock*
    mid = {"lat": (o["lat"] + d["lat"]) / 2, "lon": (o["lon"] + d["lon"]) / 2, "state": "—"}
    # naive "states traversed" guess: include origin/dest states, plus a few heuristics
    states = []
    for s in [o["state"], d["state"]]:
        if s not in states:
            states.append(s)

    # sprinkle likely corridor states for some pairs
    corridor_map = {
        ("IL", "GA"): ["IN", "TN"],
        ("IL", "TX"): ["MO"],
        ("IL", "CA"): ["MO", "CO", "AZ"],
        ("TX", "CA"): ["AZ"],
        ("CO", "CA"): ["AZ"],
    }
    key = (o["state"], d["state"])
    rev = (d["state"], o["state"])
    extra = corridor_map.get(key) or corridor_map.get(rev) or []
    for s in extra:
        if s not in states:
            states.insert(1, s)

    points = [
        {"name": origin, "lat": o["lat"], "lon": o["lon"], "type": "origin"},
        {"name": "Midpoint", "lat": mid["lat"], "lon": mid["lon"], "type": "mid"},
        {"name": dest, "lat": d["lat"], "lon": d["lon"], "type": "dest"},
    ]
    return {"points": points, "states": states, "origin": origin, "dest": dest}

def legal_pre_thinking(states: List[str], height_ft: float, gvw_lbs: int, hazmat: bool) -> Dict[str, Any]:
    """
    Simple rules engine (SIMULATED data).
    - bridge clearance check via STATE_RULES[min_bridge_ft]
    - GVW check via max_gvw_lbs
    - hazmat restrictions flags
    """
    issues = []
    advisories = []
    for st_code in states:
        rules = STATE_RULES.get(st_code)
        if not rules:
            advisories.append(f"{st_code}: No rule data (simulated dataset incomplete).")
            continue

        min_bridge = rules["min_bridge_ft"]
        if height_ft > min_bridge:
            issues.append(f"{st_code}: Height {height_ft:.1f}ft exceeds simulated min bridge clearance {min_bridge:.1f}ft.")

        if gvw_lbs > rules["max_gvw_lbs"]:
            issues.append(f"{st_code}: GVW {gvw_lbs}lbs exceeds max {rules['max_gvw_lbs']}lbs.")

        if hazmat and rules["hazmat_restrictions"]:
            issues.append(f"{st_code}: Hazmat flagged restrictions: {', '.join(rules['hazmat_restrictions'])} (simulated).")

        # add some non-blocking advisories
        if st_code == "CO":
            advisories.append("CO: Mountain pass weather can force chain requirements (not checked in this prototype).")
        if st_code == "CA":
            advisories.append("CA: CARB compliance can apply depending on equipment (not validated in this prototype).")

    status = "OK" if not issues else "RISK"
    return {"status": status, "issues": issues, "advisories": advisories, "data_note": "Rules + bridge clearances are simulated."}

def compliance_alerts(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Basic compliance alerts:
    - Missing required inspection docs
    - Expiring soon (<= 30 days)
    - Expired
    """
    alerts = []
    today = date.today()

    # Required doc presence
    present_cats = {d["category"] for d in docs}
    for cat, label in INSPECTION_REQUIRED_DOCS:
        if cat not in present_cats:
            alerts.append({"severity": "HIGH", "title": "Missing inspection doc", "detail": f"{label} ({cat}) not found."})

    # Expiry alerts
    for d in docs:
        exp = d.get("expiry_date")
        if not exp:
            continue
        if exp < today:
            alerts.append({"severity": "HIGH", "title": "Document expired", "detail": f"{d['category']}: {d['display_name']} expired on {exp.isoformat()}."})
        elif exp <= today + timedelta(days=30):
            alerts.append({"severity": "MED", "title": "Document expiring soon", "detail": f"{d['category']}: {d['display_name']} expires {exp.isoformat()}."})

    # Sort by severity
    sev_rank = {"HIGH": 0, "MED": 1, "LOW": 2}
    alerts.sort(key=lambda a: sev_rank.get(a["severity"], 9))
    return alerts

# -----------------------------
# Session state init
# -----------------------------

def init_state():
    if "tier" not in st.session_state:
        st.session_state.tier = TIER_FREE
    if "docs" not in st.session_state:
        st.session_state.docs = []  # list of dicts
    if "current_location" not in st.session_state:
        st.session_state.current_location = "Chicago, IL"
    if "last_route" not in st.session_state:
        st.session_state.last_route = build_mock_route("Chicago, IL", "Indianapolis, IN")

init_state()

# -----------------------------
# UI helpers
# -----------------------------

def badge(text: str, color: str = "#1f77b4"):
    st.markdown(
        f"""
        <span style="
            display:inline-block;
            padding:2px 10px;
            border-radius:999px;
            background:{color};
            color:white;
            font-size:12px;
            margin-right:6px;
            ">
            {text}
        </span>
        """,
        unsafe_allow_html=True,
    )

def severity_color(sev: str) -> str:
    return {"HIGH": "#d62728", "MED": "#ff7f0e", "LOW": "#2ca02c"}.get(sev, "#7f7f7f")

def legal_guardrail_widget(city: str):
    """Legal Safety Guardrail updates based on 'current location' (city/state)."""
    state_code = CITY_DB[city]["state"]
    rules = STATE_RULES.get(state_code, {})
    st.subheader("Legal Safety Guardrail")
    cols = st.columns([1, 1, 1])
    with cols[0]:
        badge(f"Location: {city}", "#444")
    with cols[1]:
        badge(f"State: {state_code}", "#444")
    with cols[2]:
        badge("Data: SIMULATED", "#6a5acd")

    if not rules:
        st.warning("No rule data for this state in the prototype dataset.")
        return

    st.write(
        {
            "max_gvw_lbs": rules["max_gvw_lbs"],
            "min_bridge_clearance_ft": rules["min_bridge_ft"],
            "hazmat_restrictions": rules["hazmat_restrictions"] or "None",
        }
    )
    st.caption("Guardrail is a rules snapshot. In production this would be derived from live state regs + route context.")

def render_map(route: Dict[str, Any], current_city: str):
    """Map interface (mock route line + current location marker)."""
    pts = route["points"]
    df_pts = pd.DataFrame(
        [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "type": p["type"]} for p in pts]
    )
    cur = CITY_DB[current_city]
    df_cur = pd.DataFrame([{"name": f"Current: {current_city}", "lat": cur["lat"], "lon": cur["lon"], "type": "current"}])

    # Line from origin to dest
    line = [{
        "path": [[pts[0]["lon"], pts[0]["lat"]], [pts[-1]["lon"], pts[-1]["lat"]]],
        "color": [30, 144, 255],
    }]
    df_line = pd.DataFrame(line)

    layer_line = pdk.Layer(
        "PathLayer",
        df_line,
        get_path="path",
        get_color="color",
        width_scale=20,
        width_min_pixels=3,
    )
    layer_pts = pdk.Layer(
        "ScatterplotLayer",
        df_pts,
        get_position=["lon", "lat"],
        get_radius=9000,
        get_fill_color="[255, 140, 0]",
        pickable=True,
    )
    layer_cur = pdk.Layer(
        "ScatterplotLayer",
        df_cur,
        get_position=["lon", "lat"],
        get_radius=12000,
        get_fill_color="[220, 20, 60]",
        pickable=True,
    )

    view = pdk.ViewState(
        latitude=(pts[0]["lat"] + pts[-1]["lat"]) / 2,
        longitude=(pts[0]["lon"] + pts[-1]["lon"]) / 2,
        zoom=4.2,
        pitch=0,
    )

    r = pdk.Deck(
        layers=[layer_line, layer_pts, layer_cur],
        initial_view_state=view,
        tooltip={"text": "{name}"},
        map_style=None,  # open basemap default
    )
    st.pydeck_chart(r, use_container_width=True)
    st.caption("Map + routing are mock visuals. Swap in Mapbox/HERE/Google for real truck-safe routing later.")

# -----------------------------
# Sidebar
# -----------------------------

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.sidebar.title("Modules")
module = st.sidebar.radio(
    "Go to",
    ["Digital Folder", "Trip Planner", "Compliance Monitor", "Subscription Billing"],
    index=0
)

st.sidebar.divider()
st.sidebar.subheader("Account / Tier")
tier = st.sidebar.selectbox("Subscription tier (demo)", [TIER_FREE, TIER_PRO], index=0 if st.session_state.tier == TIER_FREE else 1)
st.session_state.tier = tier
features = tier_features(tier)

if tier == TIER_FREE:
    st.sidebar.info("Free: basic trip planning + basic alerts. No Inspection Mode, no Auto-OCR.")
else:
    st.sidebar.success("Pro: Auto-OCR, Inspection Mode, advanced trip checks (all mocked in this prototype).")

st.sidebar.divider()
st.sidebar.subheader("Truck Context")
st.session_state.current_location = st.sidebar.selectbox("Current location (simulated GPS)", list(CITY_DB.keys()), index=list(CITY_DB.keys()).index(st.session_state.current_location))
truck_height_ft = st.sidebar.slider("Vehicle height (ft)", min_value=11.0, max_value=15.0, value=13.6, step=0.1)
truck_gvw = st.sidebar.selectbox("GVW (lbs)", [70000, 75000, 80000, 85000, 90000], index=2)
truck_hazmat = st.sidebar.checkbox("Hazmat", value=False)

# -----------------------------
# Top header and guardrail
# -----------------------------

st.title(APP_TITLE)
st.caption("Prototype focus: Digital Folder + Trip Planner + Compliance Alerts + Subscription gating. OCR & route data are simulated.")

top_cols = st.columns([1.2, 1.0])
with top_cols[0]:
    legal_guardrail_widget(st.session_state.current_location)
with top_cols[1]:
    st.subheader("Real-time Map Interface")
    render_map(st.session_state.last_route, st.session_state.current_location)

st.divider()

# -----------------------------
# Digital Folder
# -----------------------------

def view_digital_folder():
    st.header("Digital Folder")
    st.write("Upload docs, auto-categorize, and (Pro) auto-extract fields for compliance + inspection workflows.")

    upload_cols = st.columns([1.2, 0.8])
    with upload_cols[0]:
        st.subheader("Document Upload Drop Zone")
        files = st.file_uploader(
            "Drop PDFs/images here (prototype stores locally).",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )

        if files:
            for f in files:
                path = load_bytes_to_disk(f)
                category = guess_category(f.name)
                extracted = {}
                expiry = None

                if features["auto_ocr"]:
                    extracted = simulate_ocr_extract(f.name, category)
                    expiry = parse_expiry(extracted)
                else:
                    # still store basic metadata; user can manually set expiry
                    extracted = {"_extraction_mode": "NONE", "notes": "Upgrade to Pro for Auto-OCR extraction."}

                doc_rec = {
                    "id": str(uuid.uuid4()),
                    "display_name": f.name,
                    "category": category,
                    "stored_path": path,
                    "uploaded_at": now_dt().isoformat(timespec="seconds"),
                    "expiry_date": expiry,
                    "extracted": extracted,
                }
                st.session_state.docs.append(doc_rec)

            st.success(f"Uploaded {len(files)} file(s).")

    with upload_cols[1]:
        st.subheader("Quick Actions")
        if st.button("Seed sample docs (demo)"):
            # Seed a few docs with simulated expiries
            seed = [
                ("CDL_driver_EXP_2027-01-01.pdf", "CDL"),
                ("MEDCARD_EXP_2026-02-01.pdf", "MEDCARD"),
                ("INS_policy_EXP_2026-01-20.pdf", "INS"),
                ("REG_trailer_EXP_2026-07-01.pdf", "REG"),
                ("ELD_summary_EXP_2026-01-10.pdf", "ELD"),
            ]
            for name, cat in seed:
                extracted = simulate_ocr_extract(name, cat) if features["auto_ocr"] else {"_extraction_mode": "NONE"}
                exp = parse_expiry(extracted) if features["auto_ocr"] else (date.today() + timedelta(days=120))
                st.session_state.docs.append({
                    "id": str(uuid.uuid4()),
                    "display_name": name,
                    "category": cat,
                    "stored_path": "(seeded)",
                    "uploaded_at": now_dt().isoformat(timespec="seconds"),
                    "expiry_date": exp,
                    "extracted": extracted,
                })
            st.success("Seeded sample docs.")

        if st.button("Clear all docs"):
            st.session_state.docs = []
            st.warning("All documents cleared from session (uploaded files may still exist on disk).")

    st.divider()
    st.subheader("Folder View")

    if not st.session_state.docs:
        st.info("No documents yet. Upload files or seed sample docs.")
        return

    # Table view
    df = pd.DataFrame([
        {
            "Category": d["category"],
            "Name": d["display_name"],
            "Expiry": fmt_date(d.get("expiry_date")),
            "Uploaded": d["uploaded_at"],
            "Extraction": d["extracted"].get("_extraction_mode", "—"),
        }
        for d in st.session_state.docs
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detail view
    st.subheader("Document Detail")
    idx = st.selectbox("Select a document", list(range(len(st.session_state.docs))), format_func=lambda i: f"{st.session_state.docs[i]['category']} — {st.session_state.docs[i]['display_name']}")
    doc = st.session_state.docs[idx]

    det_cols = st.columns([1, 1])
    with det_cols[0]:
        st.write({"category": doc["category"], "name": doc["display_name"], "uploaded_at": doc["uploaded_at"], "stored_path": doc["stored_path"]})
        if not doc.get("expiry_date"):
            st.warning("No expiry date set.")
        else:
            st.write({"expiry_date": doc["expiry_date"].isoformat()})
        if st.button("Set expiry to +90 days (demo)", key=f"setexp_{doc['id']}"):
            doc["expiry_date"] = date.today() + timedelta(days=90)
            st.success("Expiry updated.")

    with det_cols[1]:
        st.write("Extracted Fields")
        st.json(doc.get("extracted", {}))

# -----------------------------
# Trip Planner
# -----------------------------

def view_trip_planner():
    st.header("Trip Planner (Truck-Safe Routing + Legal Pre-Thinking)")
    st.write("This prototype draws a mock route line and runs a simulated feasibility check using mocked state rules + bridge clearances.")

    cols = st.columns([1, 1])
    with cols[0]:
        origin = st.selectbox("Origin", list(CITY_DB.keys()), index=list(CITY_DB.keys()).index("Chicago, IL"))
    with cols[1]:
        dest = st.selectbox("Destination", list(CITY_DB.keys()), index=list(CITY_DB.keys()).index("Indianapolis, IN"))

    adv = st.expander("Advanced options (Pro gated)", expanded=False)
    with adv:
        if not features["trip_planner_advanced"]:
            st.info("Upgrade to Pro to unlock advanced trip checks (still mocked in this prototype).")
        avoid_tolls = st.checkbox("Avoid tolls", value=False, disabled=not features["trip_planner_advanced"])
        prefer_highways = st.checkbox("Prefer highways", value=True, disabled=not features["trip_planner_advanced"])
        st.caption("These flags are placeholders for real routing API parameters.")

    if st.button("Plan Route"):
        route = build_mock_route(origin, dest)
        st.session_state.last_route = route

        st.subheader("Route Summary")
        st.write({"origin": origin, "dest": dest, "states_traversed": route["states"], "routing_mode": "MOCK"})

        # Legal pre-thinking check
        if features["trip_planner_advanced"]:
            result = legal_pre_thinking(route["states"], height_ft=truck_height_ft, gvw_lbs=int(truck_gvw), hazmat=truck_hazmat)
        else:
            # basic check only (still useful)
            result = legal_pre_thinking(route["states"], height_ft=truck_height_ft, gvw_lbs=int(truck_gvw), hazmat=False)

        status = result["status"]
        if status == "OK":
            st.success("Legal Pre-Thinking: OK (based on simulated rule data).")
        else:
            st.error("Legal Pre-Thinking: RISK (based on simulated rule data).")

        st.caption(result["data_note"])
        if result["issues"]:
            st.subheader("Blocking / Risk Issues")
            for issue in result["issues"]:
                st.write(f"• {issue}")
        if result["advisories"]:
            st.subheader("Advisories")
            for adv in result["advisories"]:
                st.write(f"• {adv}")

        st.subheader("Map Preview")
        render_map(route, st.session_state.current_location)

    st.divider()
    st.subheader("Truck-Safe Routing API (future)")
    st.code(
        """
# Placeholder integration points (swap in later):
# - MAPBOX_TOKEN=...
# - HERE_API_KEY=...
# - GOOGLE_MAPS_KEY=...

# Implement:
# 1) geocode(origin/dest)
# 2) request truck-specific route (height/weight/hazmat)
# 3) enrich with restrictions, bridge clearances, state regs
# 4) persist trip + alerts
        """.strip(),
        language="text",
    )

# -----------------------------
# Compliance Monitor
# -----------------------------

def view_compliance_monitor():
    st.header("Compliance Monitor")
    st.write("Alerts are derived from required inspection docs + expirations. This is a basic rules engine you can expand.")

    docs = st.session_state.docs
    alerts = compliance_alerts(docs) if features["compliance_alerts"] else []

    a_cols = st.columns([1.2, 0.8])
    with a_cols[0]:
        st.subheader("Active Alerts")
        if not alerts:
            st.success("No alerts detected.")
        else:
            for a in alerts[:30]:
                badge(a["severity"], severity_color(a["severity"]))
                st.write(f"**{a['title']}** — {a['detail']}")

    with a_cols[1]:
        st.subheader("Inspection Mode (Pro)")
        if not features["inspection_mode"]:
            st.info("Upgrade to Pro to enable Inspection Mode (1-click checklist + required doc pack).")
        else:
            st.success("Inspection Mode enabled.")
            st.write("Required documents checklist:")
            present = {d["category"] for d in docs}
            for cat, label in INSPECTION_REQUIRED_DOCS:
                ok = cat in present
                st.write(("✅" if ok else "❌") + f" {label} ({cat})")

            st.divider()
            st.write("Generate an 'inspection packet' (prototype):")
            if st.button("Build inspection packet"):
                packet = []
                for cat, _label in INSPECTION_REQUIRED_DOCS:
                    matches = [d for d in docs if d["category"] == cat]
                    if matches:
                        packet.append({"category": cat, "name": matches[-1]["display_name"], "path": matches[-1]["stored_path"]})
                    else:
                        packet.append({"category": cat, "name": None, "path": None})
                st.json({"packet": packet, "generated_at": now_dt().isoformat(timespec="seconds"), "mode": "PROTOTYPE"})

    st.divider()
    st.subheader("Compliance Rules Engine (prototype)")
    st.caption("Today it checks: missing required docs + expiry windows. Next steps: DOT inspection workflows, CVSA levels, ELD/HOS, permit boundaries, and jurisdictional alerts.")

# -----------------------------
# Subscription Billing
# -----------------------------

def view_subscription_billing():
    st.header("Subscription Billing (Demo Gating)")
    st.write("This is a UI + feature flag demo. In production: Stripe Billing + webhooks + entitlements service.")

    st.subheader("Current Tier")
    if st.session_state.tier == TIER_FREE:
        badge("FREE", "#7f7f7f")
    else:
        badge("PRO", "#2ca02c")

    st.subheader("Entitlements")
    ent = tier_features(st.session_state.tier)
    st.json(ent)

    st.divider()
    st.subheader("Stripe integration plan (production)")
    st.write(
        """
- Frontend: Checkout + Customer Portal
- Backend: Stripe webhooks -> update `subscriptions` + `entitlements`
- Access control: feature flags enforced server-side (not just UI)
- Storage: docs in S3 (private) + metadata in Postgres
- OCR: async pipeline (queue worker) -> extracted fields indexed for search/alerts
        """
    )

# -----------------------------
# Route modules
# -----------------------------

if module == "Digital Folder":
    view_digital_folder()
elif module == "Trip Planner":
    view_trip_planner()
elif module == "Compliance Monitor":
    view_compliance_monitor()
elif module == "Subscription Billing":
    view_subscription_billing()

# Footer
st.divider()
st.caption("Prototype note: Route data, bridge clearances, and state rules are simulated. Replace mock datasets with authoritative sources + a truck routing API before operational use.")
