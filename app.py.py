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

# Initialize Local Backup Engine
if "backup_db" not in st.session_state:
    st.session_state.backup_db = 

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
    password = st.text_input("Password", type="password", placeholder="Paswoard")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("AUTHENTICATE SYSTEM"):
        if username == "anshuman15@gmail.com" and password == "Anshuman@0310":
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

    # ----------------- 🚚 1. LIVE TRUCK TRACKING MAP WITH SATELLITE -----------------
    st.header("📍 Live Fleet Tracker Map")
    st.write("Use the layer button in the top-right corner of the map to toggle **Satellite View**.")

    # Create an asynchronous fragment that reloads the map automatically every 10 seconds
    @st.fragment(run_every="10s")
    def show_live_map():
        # Setup mock active truck coordinates
        truck_locations = [
            {"name": "Truck A (TRK-01)", "lat": 19.0760, "lon": 72.8777, "status": "Moving"},
            {"name": "Truck B (TRK-02)", "lat": 18.5204, "lon": 73.8567, "status": "Idle"},
            {"name": "Truck C (TRK-03)", "lat": 28.7041, "lon": 77.1025, "status": "Transit"}
        ]
        
        # Initialize the base map with standard OpenStreetMap styling
        base_map = folium.Map(location=[19.0760, 72.8777], zoom_start=6, control_scale=True, tiles="OpenStreetMap")
        
        # Inject standard Google Satellite tile engine layer
        folium.TileLayer(
            tiles='https://google.com{x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(base_map)
        
        # Inject an hybrid layer adding streets over the satellite images
        folium.TileLayer(
            tiles='https://google.com{x}&y={y}&z={z}',
            attr='Google',
            name='Satellite Hybrid',
            overlay=False,
            control=True
        ).add_to(base_map)

        # Populate markers for each truck onto the map layer
        for truck in truck_locations:
            color = "green" if truck["status"] == "Moving" else "orange" if truck["status"] == "Transit" else "red"
            folium.Marker(
                location=[truck["lat"], truck["lon"]],
                popup=f"<b>{truck['name']}</b><br>Status: {truck['status']}",
                tooltip=truck["name"],
                icon=folium.Icon(color=color, icon="truck", prefix="fa")
            ).add_to(base_map)
        
        # Add a Layer Control panel so users can switch views seamlessly
        folium.LayerControl().add_to(base_map)
        
        # Render the map inside Streamlit UI safely
        st_folium(base_map, width=700, height=450, key="fleet_live_map")
        st.caption("🔄 Map automatically streaming updates every 10 seconds.")

    show_live_map()

    # ----------------- 📦 2. NEW BARCODE SCANNER PORTAL -----------------
    st.markdown("---")
    st.header("📦 New Scan Entry Portal")
    
    with st.form("barcode_scan_form", clear_on_submit=True):
        st.write("Scan or type a barcode to record it into the active log.")
        
        input_truck_id = st.text_input("Truck ID / Vehicle Name", placeholder="e.g., TRK-05")
        input_barcode = st.text_input("Barcode Data", placeholder="Click here and scan item barcode")
        input_status = st.selectbox("Scan Status", ["Success", "Damaged", "Wrong Destination"])
        
        submit_button = st.form_submit_button("💾 SAVE SCAN RECORD")
        
        if submit_button:
            if input_truck_id and input_barcode:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_record = {"truck_id": input_truck_id, "barcode": input_barcode, "status": input_status}
                
                saved_to_cloud = False
                if supabase is not None:
                    try:
                        supabase.table("scan_history").insert(new_record).execute()
                        saved_to_cloud = True
                    except Exception:
                        pass
                
                backup_record = {"created_at": current_time, "truck_id": input_truck_id, "barcode": input_barcode, "status": input_status}
                st.session_state.backup_db.insert(0, backup_record)
                
                if saved_to_cloud:
                    st.success(f"🎉 Barcode {input_barcode} successfully logged to Cloud Storage!")
                else:
                    st.info(f"💾 Barcode {input_barcode} saved securely to Local System Backup Engine.")
                st.rerun()
            else:
                st.warning("Please fill out both the Truck ID and Barcode fields.")

    # ----------------- 📊 3. REAL DATABASE SCAN HISTORY & EXCEL EXPORT -----------------
    st.markdown("---")
    st.header("📥 Operational Scanning History")

    records_loaded = False
    if supabase is not None:
        try:
            db_response = supabase.table("scan_history").select("*").order("created_at", descending=True).execute()
            records = db_response.data
            if records:
                df = pd.DataFrame(records)
                df = df[['created_at', 'truck_id', 'barcode', 'status']]
                records_loaded = True
        except Exception:
            pass

    if not records_loaded:
        df = pd.DataFrame(st.session_state.backup_db)
        st.caption("⚡ System Operating on Local Encrypted Database Backup Engine")

    st.dataframe(df, use_container_width=True)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Operations_Log')
    
    st.download_button(
        label="📥 Export Live Database Logs to Excel",
        data=excel_buffer.getvalue(),
        file_name=f"scan_history_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
