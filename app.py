import streamlit as st
import pandas as pd
import datetime
import io
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

# ----------------- 📧 AUTOMATED LOCATION EMAIL ENGINE -----------------
def send_location_email(truck_id, barcode, status, lat, lon, address, driver_mobile, history_list=None):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return False
        
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 FLEET ALERT: Truck [{truck_id}] - Scan Status Update"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SUPERVISOR_EMAIL
        
        google_maps_link = f"https://google.com{lat},{lon}"
        
        # Generates history HTML rows tracking Number Plate, Mobile Contact, Pickup, and Delivery fields
        history_html_rows = ""
        if history_list:
            for entry in history_list[:5]:  # Show latest 5 historical log actions
                history_html_rows += f"""
                <tr style="border-bottom: 1px solid #e2e8f0; font-size: 13px;">
                    <td style="padding: 8px 0; color: #475569;">{entry.get('created_at', 'N/A')}</td>
                    <td style="padding: 8px 0; font-weight: bold; color: #1e293b;">\ud83d\ude9a {entry.get('truck_id', 'N/A')}</td>
                    <td style="padding: 8px 0; color: #2563eb;">\ud83d\udcf1 {entry.get('driver_mobile', 'N/A')}</td>
                    <td style="padding: 8px 0; color: #0284c7; font-size: 12px; font-weight: 500;">\ud83d\udccd {entry.get('pickup_location', 'Pending')}</td>
                    <td style="padding: 8px 0; color: #16a34a; font-size: 12px; font-weight: 500;">\ud83c\udfc1 {entry.get('delivery_location', 'Pending')}</td>
                    <td style="padding: 8px 0; font-family: monospace; font-size: 12px;">{entry.get('barcode', 'N/A')}</td>
                    <td style="padding: 8px 0; font-weight: bold; color: #e43f5a;">{entry.get('status', 'N/A')}</td>
                </tr>
                """
        else:
            history_html_rows = '<tr><td colspan="7" style="padding: 10px 0; text-align: center; color: #94a3b8; font-size: 13px;">No prior history found.</td></tr>'

        html_body = f"""
        <html>
            <body style="font-family: 'Segoe UI', sans-serif; background-color: #f8fafc; padding: 20px; color: #1e293b;">
                <div style="max-width: 750px; margin: 0 auto; background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, #1f4068, #162447); padding: 24px; text-align: center; color: white;">
                        <h2 style="margin: 0; font-size: 22px; letter-spacing: 1px;">\ud83d\ude9a FLEET OPERATIONS ALERT</h2>
                        <p style="margin: 4px 0 0 0; color: #cbd5e1; font-size: 14px;">Real-Time Asset Scan Update Logged</p>
                    </div>
                    <div style="padding: 24px;">
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold; color: #64748b;">Truck Number Plate:</td><td style="padding: 10px 0; text-align: right; font-weight: bold; color: #1e293b; font-size: 16px;">🚨 {truck_id}</td></tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold; color: #64748b;">Driver Mobile No:</td><td style="padding: 10px 0; text-align: right; font-weight: bold; color: #2563eb;">\ud83d\udcf1 {driver_mobile}</td></tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold; color: #64748b;">Barcode SKU:</td><td style="padding: 10px 0; text-align: right; font-family: monospace; font-size: 14px; background: #f1f5f9; padding: 4px 8px; border-radius: 4px;">{barcode}</td></tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold; color: #64748b;">Update Event:</td><td style="padding: 10px 0; text-align: right; color: #e43f5a; font-weight: bold;">{status}</td></tr>
                            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 10px 0; font-weight: bold; color: #64748b;">Live Lat / Lon:</td><td style="padding: 10px 0; text-align: right; font-family: monospace;">{lat:.4f}, {lon:.4f}</td></tr>
                            <tr><td style="padding: 10px 0; font-weight: bold; color: #64748b;">Resolved Address:</td><td style="padding: 10px 0; text-align: right; font-size: 14px;">{address}</td></tr>
                        </table>
                        
                        <div style="text-align: center; margin: 25px 0;">
                            <a href="{google_maps_link}" style="background-color: #e43f5a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; box-shadow: 0 4px 12px rgba(228,63,90,0.3);">\ud83d\uddfa\ufe0f TRACK LIVE LOCATION ON MAP</a>
                        </div>
                        
                        <div style="border-radius: 8px; overflow: hidden; border: 1px solid #cbd5e1; margin-top: 15px; margin-bottom: 25px;">
                            <img src="https://google.com{lat},{lon}&zoom=13&size=600x300&maptype=roadmap&markers=color:blue%7Clabel:T%7C{lat},{lon}&sensor=false" alt="Live Location Map Image" style="width: 100%; height: auto; display: block;" />
                        </div>

                        <h3 style="font-size: 16px; color: #162447; margin: 0 0 10px 0; border-bottom: 2px solid #1f4068; padding-bottom: 5px;">\ud83d\udcca Recent Operational Logs History</h3>
                        <table style="width: 100%; border-collapse: collapse; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 2px solid #cbd5e1; font-size: 11px; color: #64748b; text-transform: uppercase;">
                                    <th style="padding-bottom: 6px;">Timestamp</th>
                                    <th style="padding-bottom: 6px;">1. Truck No.</th>
                                    <th style="padding-bottom: 6px;">2. Driver Mob</th>
                                    <th style="padding-bottom: 6px;">3. Product Picked At</th>
                                    <th style="padding-bottom: 6px;">4. Delivered At</th>
                                    <th style="padding-bottom: 6px;">Barcode</th>
                                    <th style="padding-bottom: 6px;">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history_html_rows}
                            </tbody>
                        </table>
                    </div>
                    <div style="background: #f1f5f9; padding: 16px; text-align: center; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0;">
                        This email was systematically generated by Fleet Command Dashboard Terminal Sync Layers.
                    </div>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [SUPERVISOR_EMAIL], msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

# ----------------- \ud83c\udfa8 PREMIUM SECURITY INTERFACE -----------------
def login_page():
    # FIXED: Re-enforced flawless triple-quoted closures to clear compilation flags
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #1f4068 0%, #162447 100%); }
        h1 { color: #ffffff !important; text-align: center; font-family: 'Segoe UI', sans-serif; font-weight: 700; margin-bottom: 0px; }
        div.stButton > button:first-child { background-color: #e43f5a !important; color: white !important; width: 100%; border-radius: 8px; border: none; height: 45px; font-size: 16px; font-weight: bold; transition: 0.3s; }

