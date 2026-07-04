import streamlit as st
import pandas as pd
import datetime
import io
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

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

# Start with an empty local list tracking database
if "backup_db" not in st.session_state:
    st.session_state.backup_db = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Reverse Geocoding translation script (Lat/Lon -> Real Physical Address Name)
def get_readable_address(lat, lon):
    try:
        geolocator = Nominatim(user_agent="fleet_command_dashboard")
        location = geolocator.reverse((lat, lon), timeout=5)
        if location and location.address:
            parts = location.address.split(",")
            return ", ".join(parts[:3]).strip()
    except Exception:
        pass
    return f"Location Pin ({lat}, {lon})"

# ----------------- 🎨 PREMIUM SECURITY INTERFACE -----------------
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
    # Top header columns to position the Log Out button directly in the corner
    top_col1, top_col2 = st.columns([4, 1])
    
    with top_col1:
        st.title("📊 Live Operations Dashboard")
        
    with top_col2:
        st.write("<style>div.stButton > button {width: 100%; margin-top: 15px;}</style>", unsafe_allow_html=True)
        if st.button("🚪 Log Out", help="Exit the system secure session"):
            st.session_state.logged_in = False
            st.rerun()

    # ----------------- 🚚 1. MAP DRAWER ROUTING LAYER -----------------
    st.header("📍 Live Fleet Tracker Map")
    
    @st.fragment(run_every="10s")
    def show_live_map():
        base_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="OpenStreetMap")
        folium.TileLayer('https://google.com{x}&y={y}&z={z}', attr='Google', name='Satellite Hybrid', overlay=False).add_to(base_map)

        if st.session_state.backup_db:
            df_map = pd.DataFrame(st.session_state.backup_db)
            for _, row in df_map.iterrows():
                if pd.notna(row.get('p_lat')) and pd.notna(row.get('p_lon')):
                    folium.Marker(
                        location=[row['p_lat'], row['p_lon']],
                        popup=f"<b>Origin Pickup</b><br>{row['pickup_location']}",
                        icon=folium.Icon(color="blue", icon="play", prefix="fa")
                    ).add_to(base_map)
                    
                    if pd.notna(row.get('d_lat')) and pd.notna(row.get('d_lon')):
                        folium.Marker(
                            location=[row['d_lat'], row['d_lon']],
                            popup=f"<b>Final Destination</b><br>{row['delivery_location']}",
                            icon=folium.Icon(color="green", icon="stop", prefix="fa")
                        ).add_to(base_map)
                        
                        folium.PolyLine(
                            locations=[[row['p_lat'], row['p_lon']], [row['d_lat'], row['d_lon']]],
                            color="#ff4b5c",
                            weight=4,
                            opacity=0.8
                        ).add_to(base_map)

        folium.LayerControl().add_to(base_map)
        st_folium(base_map, width=700, height=400, key="fleet_live_map")

    show_live_map()

    # ----------------- 📦 2. LIVE ROUTE SCANNER PORTAL -----------------
    st.markdown("---")
    st.header("📦 Live Scan Route Portal")
    
    st.write("📍 **Capture Current Live Coordinates:**")
    col1, col2 = st.columns(2)
    with col1:
        sim_lat = st.number_input("Current Lat", value=19.0760, format="%.4f")
    with col2:
        sim_lon = st.number_input("Current Lon", value=72.8777, format="%.4f")

    with st.form("barcode_scan_form", clear_on_submit=True):
        input_truck_id = st.text_input("Truck ID / Vehicle Name", placeholder="Enter your actual Truck plate/ID")
        input_barcode = st.text_input("Barcode Data", placeholder="Click here and scan active item barcode")
        input_status = st.selectbox("Update Trip Status", ["Picked Up (At Origin)", "Delivered (At Destination)"])
        
        submit_button = st.form_submit_button("💾 SAVE ROUTE SCAN TO DATABASE")
        
        if submit_button:
            if input_truck_id and input_barcode:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with st.spinner("Resolving coordinate data into exact physical address..."):
                    resolved_address = get_readable_address(sim_lat, sim_lon)
                
                existing_match = None
                for idx, entry in enumerate(st.session_state.backup_db):
                    if entry["truck_id"] == input_truck_id and entry["barcode"] == input_barcode:
                        existing_match = idx
                        break

                if "Picked Up" in input_status:
                    new_record = {
                        "created_at": current_time,
                        "truck_id": input_truck_id, "barcode": input_barcode, "status": "In Transit",
                        "pickup_location": resolved_address, "delivery_location": "Pending Delivery",
                        "p_lat": sim_lat, "p_lon": sim_lon, "d_lat": None, "d_lon": None
                    }
                    st.session_state.backup_db.insert(0, new_record)
                else:
                    if existing_match is not None:
                        st.session_state.backup_db[existing_match]["status"] = "Delivered"
                        st.session_state.backup_db[existing_match]["delivery_location"] = resolved_address
                        st.session_state.backup_db[existing_match]["d_lat"] = sim_lat
                        st.session_state.backup_db[existing_match]["d_lon"] = sim_lon
                    else:
                        new_record = {
                            "created_at": current_time,
                            "truck_id": input_truck_id, "barcode": input_barcode, "status": "Delivered",
                            "pickup_location": "Direct Delivery (No Pickup Logged)", "delivery_location": resolved_address,
                            "p_lat": None, "p_lon": None, "d_lat": sim_lat, "d_lon": sim_lon
                        }
                        st.session_state.backup_db.insert(0, new_record)
                
                if supabase is not None:
                    try:
                        cloud_record = {
                            "truck_id": input_truck_id, "barcode": input_barcode, "status": input_status,
                            "pickup_location": resolved_address if "Picked Up" in input_status else "Updated",
                            "delivery_location": resolved_address if "Delivered" in input_status else "Pending Delivery"
                        }
                        supabase.table("scan_history").insert(cloud_record).execute()
                    except Exception:
                        pass
                
                st.success("🎉 Route logistics data logged and address fields updated successfully!")
                st.rerun()
            else:
                st.warning("Please fill out both fields before saving.")

    # ----------------- 📊 3. FORCE VISIBLE HISTORY GRID -----------------
    st.markdown("---")
    st.header("📥 Complete Route Scan Logs")

    # If list is empty, build a clean structural layout with empty rows
    if st.session_state.backup_db:
        df = pd.DataFrame(st.session_state.backup_db)
    else:
        df = pd.DataFrame(columns=['created_at', 'truck_id', 'barcode', 'status', 'pickup_location', 'delivery_location'])

    clean_df = df[['created_at', 'truck_id', 'barcode', 'status', 'pickup_location', 'delivery_location']]
    st.dataframe(clean_df, use_container_width=True)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
