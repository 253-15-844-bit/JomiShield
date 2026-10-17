import json
import math
import hashlib
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
import pydeck as pdk

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
RECORDS_FILE = DATA_DIR / "records.json"
ALERTS_FILE = DATA_DIR / "alerts.json"

st.set_page_config(page_title="JomiShield", page_icon="🛡️", layout="wide")

def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not RECORDS_FILE.exists():
        RECORDS_FILE.write_text(json.dumps(sample_records(), indent=2), encoding="utf-8")
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("[]", encoding="utf-8")

def sample_records():
    return [
        {
            "record_id": "JS-1001", "parcel_id": "DHAKA-MOCK-001", "district": "Demo District",
            "upazila": "Demo Upazila", "mouza": "Demo Mouza", "dag": "125", "khatian": "56",
            "owner_label": "Sample Owner A", "area_decimal": 10.0, "status": "Reference",
            "lat": 23.8103, "lon": 90.4125, "notes": "Synthetic demonstration record only.",
            "updated_at": "2026-10-01 10:00"
        },
        {
            "record_id": "JS-1002", "parcel_id": "DHAKA-MOCK-002", "district": "Demo District",
            "upazila": "Demo Upazila", "mouza": "Demo Mouza", "dag": "220", "khatian": "89",
            "owner_label": "Sample Owner B", "area_decimal": 6.5, "status": "Reference",
            "lat": 23.8140, "lon": 90.4180, "notes": "Synthetic demonstration record only.",
            "updated_at": "2026-10-02 11:30"
        }
    ]

def read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

def area_units(decimal):
    return {
        "Decimal / Shotok": decimal,
        "Square feet": decimal * 435.6,
        "Square metres": decimal * 40.468564224,
        "Acres": decimal / 100.0
    }

def polygon_area_m2(coords):
    # Spherical-ish local projection: convert lon/lat to metres around mean latitude.
    if len(coords) < 3:
        return 0.0
    lat0 = math.radians(sum(lat for lat, lon in coords) / len(coords))
    pts = []
    for lat, lon in coords:
        x = math.radians(lon) * 6371000 * math.cos(lat0)
        y = math.radians(lat) * 6371000
        pts.append((x, y))
    s = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2

def to_decimal(m2):
    # 1 decimal/shotok = 40.468564224 m²
    return m2 / 40.468564224

ensure_files()
records = read_json(RECORDS_FILE, [])
alerts = read_json(ALERTS_FILE, [])

st.title("🛡️ JomiShield")
st.caption("Smart Land Protection, Mapping & Record Verification — prototype using synthetic data")
st.warning("ডেমো অ্যাপ: এখানে কেবল নমুনা/কৃত্রিম তথ্য ব্যবহার করুন। এটি সরকারি রেকর্ড যাচাই বা আইনি মালিকানা প্রমাণ করে না।")

pages = ["Overview", "Land Records", "Compare & Verify", "Map & Area", "Alerts & History", "File Fingerprint"]
page = st.sidebar.radio("Navigation", pages)

if page == "Overview":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saved records", len(records))
    c2.metric("Open alerts", sum(1 for a in alerts if a.get("status", "Open") == "Open"))
    c3.metric("Demo parcels", len(set(r.get("parcel_id") for r in records)))
    c4.metric("Prototype mode", "Synthetic data")
    st.subheader("How to try the demo")
    st.markdown("""
    1. **Land Records:** add a new reference parcel or review existing sample records.
    2. **Compare & Verify:** choose a parcel and enter changed details to trigger discrepancy checks.
    3. **Map & Area:** draw a polygon on the map by clicking several points, then calculate approximate area.
    4. **Alerts & History:** review generated alerts and mark them as reviewed.
    5. **File Fingerprint:** upload a file to calculate its SHA-256 fingerprint. This checks file changes, not document authenticity.
    """)
    st.info("Suggested demo: choose parcel DHAKA-MOCK-001, change the area from 10 to 7 decimals in Compare & Verify, and generate an alert.")

elif page == "Land Records":
    st.subheader("Land Records")
    if records:
        df = pd.DataFrame(records)
        cols = [c for c in ["record_id","parcel_id","district","upazila","mouza","dag","khatian","owner_label","area_decimal","status","updated_at"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No records yet.")
    st.markdown("### Add a synthetic reference record")
    with st.form("add_record_form"):
        col1, col2 = st.columns(2)
        parcel_id = col1.text_input("Parcel ID", value="DEMO-PARCEL-003")
        owner_label = col2.text_input("Owner label (use a fake label)", value="Sample Owner C")
        district = col1.text_input("District", value="Demo District")
        upazila = col2.text_input("Upazila", value="Demo Upazila")
        mouza = col1.text_input("Mouza", value="Demo Mouza")
        dag = col2.text_input("Dag number", value="300")
        khatian = col1.text_input("Khatian number", value="100")
        area = col2.number_input("Recorded area (decimal/shotok)", min_value=0.01, value=5.0, step=0.5)
        lat = col1.number_input("Map latitude (demo coordinate)", value=23.8103, format="%.6f")
        lon = col2.number_input("Map longitude (demo coordinate)", value=90.4125, format="%.6f")
        notes = st.text_area("Notes", value="Synthetic demonstration record only.")
        submitted = st.form_submit_button("Save reference record")
        if submitted:
            if not parcel_id.strip() or not dag.strip() or not khatian.strip():
                st.error("Parcel ID, Dag and Khatian are required.")
            elif any(r.get("parcel_id") == parcel_id.strip() for r in records):
                st.error("This Parcel ID already exists. Use a unique demo Parcel ID.")
            else:
                records.append({
                    "record_id": f"JS-{1001 + len(records)}", "parcel_id": parcel_id.strip(),
                    "district": district.strip(), "upazila": upazila.strip(), "mouza": mouza.strip(),
                    "dag": dag.strip(), "khatian": khatian.strip(), "owner_label": owner_label.strip(),
                    "area_decimal": float(area), "status": "Reference", "lat": float(lat), "lon": float(lon),
                    "notes": notes.strip(), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                write_json(RECORDS_FILE, records)
                st.success("Reference record saved.")
                st.rerun()

elif page == "Compare & Verify":
    st.subheader("Compare & Verify")
    if not records:
        st.info("Add a reference record first.")
    else:
        parcels = {f"{r['parcel_id']} | Dag {r['dag']} | {r['area_decimal']} decimal": r for r in records}
        chosen_label = st.selectbox("Select reference parcel", list(parcels.keys()))
        ref = parcels[chosen_label]
        st.markdown("#### Reference values")
        st.json({k: ref.get(k) for k in ["parcel_id","dag","khatian","owner_label","area_decimal"]})
        st.markdown("#### Enter new/updated values to compare")
        with st.form("compare_form"):
            new_owner = st.text_input("Owner label", value=ref.get("owner_label", "Sample Owner"))
            new_dag = st.text_input("Dag number", value=ref.get("dag", ""))
            new_khatian = st.text_input("Khatian number", value=ref.get("khatian", ""))
            new_area = st.number_input("Recorded area (decimal/shotok)", min_value=0.01, value=float(ref.get("area_decimal", 1.0)), step=0.5)
            new_claim = st.text_input("Claim / transaction reference (optional)", value="")
            run_compare = st.form_submit_button("Compare records")
        if run_compare:
            differences = []
            if new_owner.strip().casefold() != str(ref.get("owner_label","")).strip().casefold():
                differences.append(("Owner label", ref.get("owner_label"), new_owner.strip()))
            if new_dag.strip() != str(ref.get("dag","")).strip():
                differences.append(("Dag number", ref.get("dag"), new_dag.strip()))
            if new_khatian.strip() != str(ref.get("khatian","")).strip():
                differences.append(("Khatian number", ref.get("khatian"), new_khatian.strip()))
            delta = abs(float(new_area) - float(ref.get("area_decimal", 0)))
            if delta > 0.01:
                differences.append(("Area (decimal)", ref.get("area_decimal"), float(new_area)))
            if differences:
                alert = {
                    "alert_id": f"AL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "parcel_id": ref.get("parcel_id"),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "Open",
                    "risk_level": "Review required",
                    "claim_reference": new_claim,
                    "differences": [{"field": f, "reference": old, "submitted": new} for f, old, new in differences],
                    "message": "Record discrepancy detected. This is not proof of fraud or legal ownership."
                }
                alerts.append(alert)
                write_json(ALERTS_FILE, alerts)
                st.error("Discrepancy detected — review required.")
                st.dataframe(pd.DataFrame(alert["differences"]), use_container_width=True, hide_index=True)
                st.warning(alert["message"])
            else:
                st.success("No discrepancy found in the checked fields. This does not certify the record as genuine.")

elif page == "Map & Area":
    st.subheader("Map & Approximate Area Measurement")
    st.caption("Click at least 3 points on the map to create a parcel polygon. Measurements are estimates only.")
    st.info("For this interactive map component, internet access may be needed to load the map tiles.")
    try:
        from streamlit_folium import st_folium
        import folium
        from folium.plugins import Draw
        m = folium.Map(location=[23.8103, 90.4125], zoom_start=16, control_scale=True)
        Draw(
            export=False,
            draw_options={
                "polyline": False, "rectangle": False, "circle": False, "circlemarker": False,
                "marker": False, "polygon": {"allowIntersection": False, "showArea": True}
            },
            edit_options={"edit": True, "remove": True}
        ).add_to(m)
        map_state = st_folium(m, height=480, width=None, key="land_map", returned_objects=["all_drawings"])
        drawings = map_state.get("all_drawings") or []
        polygons = [d for d in drawings if d.get("geometry", {}).get("type") == "Polygon"]
        if polygons:
            coords_lonlat = polygons[-1]["geometry"]["coordinates"][0]
            coords = [(lat, lon) for lon, lat in coords_lonlat]
            m2 = polygon_area_m2(coords)
            dec = to_decimal(m2)
            st.success("Approximate polygon area calculated.")
            a,b,c,d = st.columns(4)
            a.metric("Square metres", f"{m2:,.2f}")
            b.metric("Square feet", f"{m2 * 10.7639104167:,.2f}")
            c.metric("Decimal / Shotok", f"{dec:,.3f}")
            d.metric("Acres", f"{dec/100:,.5f}")
            st.caption("This calculation uses a local projection approximation. For legal or cadastral measurement, use authoritative survey data.")
        else:
            st.write("Use the polygon tool in the map's toolbar, then click 3 or more boundary points and finish the polygon.")
    except Exception as e:
        st.error("The map component could not load. Check installation and internet access, then restart the app.")
        st.code(str(e))
        st.markdown("You can still use the other modules while troubleshooting the map component.")

elif page == "Alerts & History":
    st.subheader("Alerts & History")
    if not alerts:
        st.info("No alerts yet. Go to Compare & Verify and change an area or identifier to create one.")
    else:
        for i, alert in enumerate(alerts):
            with st.expander(f"{alert.get('alert_id')} · {alert.get('parcel_id')} · {alert.get('status','Open')} · {alert.get('created_at')}"):
                st.write(alert.get("message", ""))
                st.write("Risk status:", alert.get("risk_level", "Review required"))
                st.dataframe(pd.DataFrame(alert.get("differences", [])), use_container_width=True, hide_index=True)
                if alert.get("status", "Open") != "Reviewed":
                    if st.button("Mark as reviewed", key=f"review_{i}"):
                        alert["status"] = "Reviewed"
                        write_json(ALERTS_FILE, alerts)
                        st.rerun()

elif page == "File Fingerprint":
    st.subheader("File Fingerprint (SHA-256)")
    st.write("Upload a file to calculate its SHA-256 fingerprint. This can help detect whether file contents changed between two copies; it does not verify whether a document is genuine.")
    uploaded = st.file_uploader("Upload a demo file", type=None)
    if uploaded:
        digest = hashlib.sha256(uploaded.getvalue()).hexdigest()
        st.code(digest)
        st.caption("Keep the fingerprint and compare it later with a fingerprint generated from another copy of the same file.")
