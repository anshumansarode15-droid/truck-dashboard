import streamlit as st
import pandas as pd
import datetime
import io
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# ----------------- 🛠️ SYSTEM SECURITY & CONFIGURATION -----------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your-secret-anon-key")

@st.cache_resource
def init_supabase_client():
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Database Initialization Error: {e}")
        return None

supabase = init_supabase_client()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

@st.cache_data(ttl=3600)
def get_readable_address(lat, lon):
    try:
        geolocator = Nominatim(user_agent="fleet_command_dashboard_v12")
        location = geolocator.reverse((lat, lon), timeout=5)
        if location and location.address:
            parts = location.address.split(",")
            return ", ".join(parts[:3]).strip()
    except Exception:
        pass
    return f"Location Pin ({lat:.4f}, {lon:.4f})"

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
    
    with st.form("secure_auth_form"):
        username = st.text_input("Username", placeholder="Enter your operator username")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submit_auth = st.form_submit_button("AUTHENTICATE SYSTEM")
        
        if submit_auth:
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
    # FIXED: Added explicit width sizing parameters to solve modern Streamlit column syntax rules
    top_col1, top_col2 = st.columns([4, 1])
    
    with top_col1:
        st.title("📊 Live Operations Dashboard")
        
    with top_col2:
        st.write("<style>div.stButton > button {width: 100%; margin-top: 15px;}</style>", unsafe_allow_html=True)
        if st.button("🚪 Log Out", help="Exit the system secure session"):
            st.session_state.logged_in = False
            st.rerun()

    scans_data = []
    if supabase:
        try:
            response = supabase.table("fleet_scans").select("*").order("created_at", descending=True).execute()
            scans_data = response.data if response.data else []
        except Exception as e:
            st.error(f"Error fetching live fleet data: {e}")

    # ----------------- 📈 LIVE ANALYTICAL METRIC TILES -----------------
    if scans_data:
        df_metrics = pd.DataFrame(scans_data)
        total_trips = len(df_metrics)
        in_transit = len(df_metrics[df_metrics['status'] == 'In Transit'])
        delivered = len(df_metrics[df_metrics['status'] == 'Delivered'])
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric(label="📦 Active Tracked Assets", value=total_trips)
        m_col2.metric(label="🚚 Operational Trucks In Transit", value=in_transit)
        m_col3.metric(label="✅ Successful Cargo Deliveries", value=delivered)
        st.markdown("---")

    # ----------------- 🚚 1. MAP DRAWER ROUTING LAYER -----------------
    st.header("📍 Live Fleet Tracker Map")
    
    @st.fragment(run_every="10s")
    def show_live_map(data_source):
        base_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="OpenStreetMap")
        
        folium.TileLayer(
            tiles='https://google.com{x}&y={y}&z={z}', 
            attr='Google Satellite Hybrid', 
            name='Satellite Hybrid', 
            overlay=False
        ).add_to(base_map)

        if data_source:
            df_map = pd.DataFrame(data_source)
            for _, row in df_map.iterrows():
                if pd.notna(row.get('p_lat')) and pd.notna(row.get('p_lon')) and row['p_lat'] is not None:
                    folium.Marker(
                        location=[row['p_lat'], row['p_lon']],
                        popup=f"<b>Origin Pickup</b><br>{row.get('pickup_location', '')}",
                        icon=folium.Icon(color="blue", icon="play", prefix="fa")
                    ).add_to(base_map)
                    
                    if pd.notna(row.get('d_lat')) and pd.notna(row.get('d_lon')) and row['d_lat'] is not None:
                        folium.Marker(
                            location=[row['d_lat'], row['d_lon']],
                            popup=f"<b>Final Destination</b><br>{row.get('delivery_location', '')}",
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

    show_live_map(scans_data)

