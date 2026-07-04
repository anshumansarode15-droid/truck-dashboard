import streamlit as st
import pandas as pd
import datetime
import io
import folium
from streamlit_folium import st_folium

# ----------------- 🛠️ SYSTEM SECURITY & CONFIGURATION -----------------
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_secret_BwNhgBiWH42i9unHb1_Cyw_39bqW4aZ"

@st.cache_resource
def init_supabase_client():
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase_client()

# Initialize Local Backup Engine with sample route coordinates
if "backup_db" not in st.session_state:
    st.session_state.backup_db = [
        {"created_at": "2026-07-04 10:00:00", "truck_id": "TRK-01", "barcode": "890107200123", "status": "Delivered", "pickup_location": "Mumbai Hub (19.07, 72.87)", "delivery_location": "Pune Depot (18.52, 73.85)"},
        {"created_at": "2026-07-04 11:30:00", "truck_id": "TRK-02", "barcode": "750103123456", "status": "In Transit", "pickup_location": "Delhi Terminal (28.70, 77.10)", "delivery_location": "Pending Delivery"}
    ]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ----------------- 🎨 PREMIUM CUSTOMIZED LOGIN INTERFACE -----------------
def login_page():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #1f4068 0%, #162447 100%); }
        h1 { color: #ffffff !important; text-align: center; font-family: 'Segoe UI', sans-serif; font-weight: 700; margin-bottom: 0px; }
        div.stButton > button:first-child { background-color: #e43f5a !important; color: white !important; width: 100%; border-radius: 8px; border: none; height: 45px; font-size: 16px; font-weight: bold; transition: 0.3s; }
        div.stButton > button:first-child:hover { background-color: #ff4b5c !important; box-shadow: 0px 5px 15px rgba(228,63,90,0.4); }
        label { color: #ffffff !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.title("🚚 FLEET COMMAND")
    st.markdown("<p style='text-align: center; color: #cbd5e1; margin-bottom: 30px;'>Enterprise Scan & Asset Management Portal</p>", unsafe_allow_html=True)
    
    username = st.text_input("Username", placeholder="Enter your operator username")
    password = st.text_input("Password", type="password", placeholder="••••••••")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("AUTHENTICATE SYSTEM"):
        if username == "admin" and password == "securepass2026":
            st.session_state.logged_in = True
            st.success("Access Granted.")
            st.rerun()
        else:
            st.error("Access Denied: Invalid System Credentials")

# ----------------- 🚦 MAIN ROUTE CONTROL -----------------
if not st.session_state.logged_in:
    login_page()
else:
    st.sidebar.title("🛡️ System Control")
    if st.sidebar.button("Log Out of System"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📊 Live Operations Dashboard")

    # ----------------- 🚚 1. LIVE TRUCK TRACKING MAP -----------------
    st.header("📍 Live Fleet Tracker Map")
    
    @st.fragment(run_every="10s")
    def show_live_map():
        truck_locations = [
            {"name": "Truck A (TRK-01)", "lat": 19.0760, "lon": 72.8777, "status": "Moving"},
            {"name": "Truck B (TRK-02)", "lat": 18.5204, "lon": 73.8567, "status": "Idle"},
            {"name": "Truck C (TRK-03)", "lat": 28.7041, "lon": 77.1025, "status": "Transit"}
        ]
        base_map = folium.Map(location=[19.0760, 72.8777], zoom_start=6, tiles="OpenStreetMap")
        
        folium.TileLayer('https://google.com{x}&y={y}&z={z}', attr='Google', name='Satellite Hybrid', overlay=False).add_to(base_map)

        for truck in truck_locations:
            color = "green" if truck["status"] == "Moving" else "orange" if truck["status"] == "Transit" else "red"
            folium.Marker(
                location=[truck["lat"], truck["lon"]],
                popup=f"<b>{truck['name']}</b><br>Status: {truck['status']}",
                icon=folium.Icon(color=color, icon="truck", prefix="fa")
            ).add_to(base_map)
        
        folium.LayerControl().add_to(base_map)
        st_folium(base_map, width=700, height=400, key="fleet_live_map")

    show_live_map()

    # ----------------- 📦 2. UPGRADED ROUTE SCANNER PORTAL -----------------
    st.markdown("---")
    st.header("📦 Live Scan Route Portal")
    
    # Simple choice to simulate real GPS tracking locations
    st.write("📍 **Simulate Current Coordinates for testing:**")
    col1, col2 = st.columns(2)
    with col1:
        sim_lat = st.number_input("Current Lat", value=19.0760, format="%.4f")
    with col2:
        sim_lon = st.number_input("Current Lon", value=72.8777, format="%.4f")

    with st.form("barcode_scan_form", clear_on_submit=True):
        input_truck_id = st.text_input("Truck ID / Vehicle Name", placeholder="e.g., TRK-01")
        input_barcode = st.text_input("Barcode Data", placeholder="Click here and scan item barcode")
        
        # Status now matches logical transit states
        input_status = st.selectbox("Update Trip Status", ["Picked Up (At Origin)", "Delivered (At Destination)", "In Transit"])
        
        submit_button = st.form_submit_button("💾 SAVE ROUTE SCAN TO DATABASE")
        
        if submit_button:
            if input_truck_id and input_barcode:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                geo_string = f"Lat: {sim_lat}, Lon: {sim_lon}"
                
                # Logic to determine routing data based on action status selected
                p_loc = geo_string if "Picked Up" in input_status else "Logged from Hub"
                d_loc = geo_string if "Delivered" in input_status else "Pending Delivery"
                
                new_record = {
                    "truck_id": input_truck_id, 
                    "barcode": input_barcode, 
                    "status": input_status,
                    "pickup_location": p_loc,
                    "delivery_location": d_loc
                }
                
                saved_to_cloud = False
                if supabase is not None:
                    try:
                        supabase.table("scan_history").insert(new_record).execute()
                        saved_to_cloud = True
                    except Exception:
                        pass
                
                backup_record = {
                    "created_at": current_time, 
                    "truck_id": input_truck_id, 
                    "barcode": input_barcode, 
                    "status": input_status,
                    "pickup_location": p_loc,
                    "delivery_location": d_loc
                }
                st.session_state.backup_db.insert(0, backup_record)
                
                if saved_to_cloud:
                    st.success(f"🎉 Barcode recorded! Route tracking saved to cloud database.")
                else:
                    st.info(f"💾 Saved to local database backup engine.")
                st.rerun()
            else:
                st.warning("Please fill out both fields.")

    # ----------------- 📊 3. EXCEL HISTORY REPO WITH LOCATION DATA -----------------
    st.markdown("---")
    st.header("📥 Complete Route Scan Logs")

    records_loaded = False
    if supabase is not None:
        try:
            db_response = supabase.table("scan_history").select("*").order("created_at", descending=True).execute()
            records = db_response.data
            if records:
                df = pd.DataFrame(records)
                # Keep the new route tracking variables visible
                df = df[['created_at', 'truck_id', 'barcode', 'status', 'pickup_location', 'delivery_location']]
                records_loaded = True
        except Exception:
            pass

    if not records_loaded:
        df = pd.DataFrame(st.session_state.backup_db)
        st.caption("⚡ Operating on Database Backup Engine")

    st.dataframe(df, use_container_width=True)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Route_Logistics')
    
    st.download_button(
        label="📥 Download Full Route Excel Sheet",
        data=excel_buffer.getvalue(),
        file_name=f"fleet_route_report_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
