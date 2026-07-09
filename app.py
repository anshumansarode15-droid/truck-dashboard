import streamlit as st
import pandas as pd
import datetime
import io
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ----------------- 🛠️ SYSTEM SECURITY & CONFIGURATION -----------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your-secret-anon-key")

# Secure Email SMTP Credentials managed safely from your Streamlit cloud panel
SMTP_SERVER = st.secrets.get("SMTP_SERVER", "://gmail.com")
SMTP_PORT = int(st.secrets.get("SMTP_PORT", 587))
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "your-logistics-system@gmail.com")
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", "your-app-password")
SUPERVISOR_EMAIL = st.secrets.get("SUPERVISOR_EMAIL", "manager@yourcompany.com")

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

# ----------------- 📧 AUTOMATED SEPARATED EMAIL ENGINE -----------------
def send_location_email(truck_id, barcode, status, lat, lon, address, driver_mobile, history_list=None):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return False
        
    try:
        # 1. Read the separate HTML layout file from your project folder safely
        template_path = os.path.join(os.path.dirname(__file__), "email_template.html")
        if not os.path.exists(template_path):
            st.error("Email layout file error: 'email_template.html' file is missing in your repository.")
            return False
            
        with open(template_path, "r", encoding="utf-8") as file:
            html_template = file.read()
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 FLEET ALERT: Truck [{truck_id}] - Scan Status Update"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SUPERVISOR_EMAIL
        
        google_maps_link = f"https://google.com{lat},{lon}"
        
        # 2. Build explicit table row strings dynamically from the tracking loops data
        history_html_rows = ""
        if history_list:
            for entry in history_list[:5]:
                history_html_rows += f"""
                <tr style="border-bottom: 1px solid #e2e8f0; font-size: 13px;">
                    <td style="padding: 8px 0; color: #475569;">{entry.get('created_at', 'N/A')}</td>
                    <td style="padding: 8px 0; font-weight: bold; color: #1e293b;">🚛 {entry.get('truck_id', 'N/A')}</td>
                    <td style="padding: 8px 0; color: #2563eb;">📱 {entry.get('driver_mobile', 'N/A')}</td>
                    <td style="padding: 8px 0; color: #0284c7; font-size: 12px; font-weight: 500;">📍 {entry.get('pickup_location', 'Pending')}</td>
                    <td style="padding: 8px 0; color: #16a34a; font-size: 12px; font-weight: 500;">🏁 {entry.get('delivery_location', 'Pending')}</td>
                    <td style="padding: 8px 0; font-family: monospace; font-size: 12px;">{entry.get('barcode', 'N/A')}</td>
                    <td style="padding: 8px 0; font-weight: bold; color: #e43f5a;">{entry.get('status', 'N/A')}</td>
                </tr>
                """
        else:
            history_html_rows = '<tr><td colspan="7" style="padding: 10px 0; text-align: center; color: #94a3b8; font-size: 13px;">No prior history found.</td></tr>'

        # 3. Inject variables directly into the separated HTML text variables package placeholder map safely
        html_body = html_template.format(
            truck_id=truck_id,
            driver_mobile=driver_mobile,
            barcode=barcode,
            status=status,
            lat=lat,
            lon=lon,
            address=address,
            google_maps_link=google_maps_link,
            history_html_rows=history_html_rows
        )
        
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [SUPERVISOR_EMAIL], msg.as_string())
        server.quit()
        return True
    except Exception as email_err:
        st.error(f"Email routing error: {email_err}")
        return False

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
    top_col1, top_col2 = st.columns(2)
    
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
            response = supabase.table("fleet_scans").select("*").order("created_at", desc=True).execute()
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
                truck_plate = row.get('truck_id', 'Unknown Vehicle')
                mob = row.get('driver_mobile', 'No Mobile')
                
                if pd.notna(row.get('p_lat')) and pd.notna(row.get('p_lon')) and row['p_lat'] is not None:
                    folium.Marker(
                        location=[row['p_lat'], row['p_lon']],
                        popup=f"<b>Truck: {truck_plate}</b><br>Driver Mob: {mob}<br>Origin: {row.get('pickup_location', '')}",
                        tooltip=f"🚚 {truck_plate}",
                        icon=folium.Icon(color="blue", icon="play", prefix="fa")
                    ).add_to(base_map)
                    
                    if pd.notna(row.get('d_lat')) and pd.notna(row.get('d_lon')) and row['d_lat'] is not None:
                        folium.Marker(
                            location=[row['d_lat'], row['d_lon']],
                            popup=f"<b>Truck: {truck_plate}</b><br>Driver Mob: {mob}<br>Destination: {row.get('delivery_location', '')}",
                            tooltip=f"✅ {truck_plate}",
                            icon=folium.Icon(color="green", icon="stop", prefix="fa")
