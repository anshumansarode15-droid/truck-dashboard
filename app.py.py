import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from supabase import create_client, Client

# ----------------- 🛠️ SYSTEM SECURITY & CONFIGURATION -----------------
# Your actual database credentials are hardcoded here safely
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1anhnZ3dsaWZrdGZhbXBwcWRpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMxNTIzNDcsImV4cCI6MjA5ODcyODM0N30.EGIVz3gpVRIpHUDWCj0xLNvlIPL9Wu9cTeSbJdZVa4E"

# Initialize Supabase Database Client Connection
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Defining 'supabase' globally so all sections can use it
supabase = init_supabase()

# Initialize Login Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ----------------- 🎨 CUSTOMIZED LOGIN INTERFACE -----------------
def login_page():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #1f4068 0%, #162447 100%);
        }
        .login-card {
            background-color: #ffffff;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0px 10px 25px rgba(0,0,0,0.3);
            max-width: 450px;
            margin: auto;
        }
        h1 {
            color: #ffffff !important;
            text-align: center;
            font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
            font-weight: 700;
        }
        div.stButton > button:first-child {
            background-color: #e43f5a !important;
            color: white !important;
            width: 100%;
            border-radius: 8px;
            border: none;
            height: 45px;
            font-size: 16px;
            font-weight: bold;
            transition: 0.3s;
        }
        div.stButton > button:first-child:hover {
            background-color: #ff4b5c !important;
            box-shadow: 0px 5px 15px rgba(228,63,90,0.4);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.title("🚚 FLEET COMMAND")
    st.caption("<p style='text-align: center; color: #cbd5e1;'>Enterprise Scan & GPS Asset Management</p>", unsafe_allow_html=True)
    
    username = st.text_input("Username", placeholder="Enter your operator username")
    password = st.text_input("Password", type="password", placeholder="••••••••")
    
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
    st.sidebar.title("Fleet Controls")
    if st.sidebar.button("System Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📊 Live Operations Dashboard")

    # ----------------- 📦 NEW BARCODE SCANNER PORTAL -----------------
    st.header("📦 New Scan Entry Portal")
    
    with st.form("barcode_scan_form", clear_on_submit=True):
        st.write("Scan or enter a new barcode to log it to the database.")
        
        input_truck_id = st.text_input("Truck ID / Vehicle Name", placeholder="e.g., TRK-05")
        input_barcode = st.text_input("Barcode Data", placeholder="Click here and scan barcode")
        input_status = st.selectbox("Scan Status", ["Success", "Damaged", "Wrong Destination"])
        
        submit_button = st.form_submit_button("💾 SAVE SCAN TO CLOUD DATABASE")
        
        if submit_button:
            if input_truck_id and input_barcode:
                try:
                    new_record = {
                        "truck_id": input_truck_id,
                        "barcode": input_barcode,
                        "status": input_status
                    }
                    supabase.table("scan_history").insert(new_record).execute()
                    st.success(f"Successfully logged barcode {input_barcode} to the database!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save data: {e}")
            else:
                st.warning("Please fill out both the Truck ID and Barcode fields.")

    # ----------------- 📊 REAL DATABASE SCAN HISTORY -----------------
    st.header("📥 Scanning Records & Database History")

    try:
        db_response = supabase.table("scan_history").select("*").order("created_at", descending=True).execute()
        records = db_response.data
        
        if records:
            df = pd.DataFrame(records)
            df = df[['created_at', 'truck_id', 'barcode', 'status']]
            st.dataframe(df, use_container_width=True)
            
            import io
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Live_Logs')
            
            st.download_button(
                label="📥 Export Live Database Logs to Excel",
                data=excel_buffer.getvalue(),
                file_name="live_scan_history.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("The database is currently empty. Insert data into the portal above to view reports.")
    except Exception as db_err:
        st.error("Cloud Database Sync Error: Check your Supabase API Keys config.")
