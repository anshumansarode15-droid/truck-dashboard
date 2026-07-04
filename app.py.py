import streamlit as st
import sqlite3
import datetime
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configure Web Page Layout
st.set_page_config(page_title="Fleet Logistics Hub", layout="wide")

# Initialize Local Database
def init_db():
    conn = sqlite3.connect('truck_web_logistics.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT, action TEXT, timestamp TEXT, lat REAL, lon REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Top Web Header Bar
st.title(" Fleet Logistics & Asset Tracking Hub")
st.markdown("---")

# Web Sidebar Layout for Barcode Controls
st.sidebar.header("🕹️ Scanner Control Station")
barcode_input = st.sidebar.text_input("Scan Barcode Here", key="barcode_scan", placeholder="Align scanner and trigger...")
col1, col2 = st.sidebar.columns(2)
pickup_clicked = col1.button("🟢 Log Pickup", use_container_width=True)
delivery_clicked = col2.button("🔴 Log Delivery", use_container_width=True)

# Database Processing Logic
# Solapur, Maharashtra, India reference coordinates
truck_lat, truck_lon = 17.6599, 75.9064 

if (pickup_clicked or delivery_clicked) and barcode_input:
    action = "PICKUP" if pickup_clicked else "DELIVERY"
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    conn = sqlite3.connect('truck_web_logistics.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO asset_history (barcode, action, timestamp, lat, lon) VALUES (?, ?, ?, ?, ?)',
                   (barcode_input, action, now_time, truck_lat, truck_lon))
    conn.commit()
    conn.close()
    st.sidebar.success(f"Successfully logged {action} for {barcode_input}!")

# Main Web Layout Split (Left = Map, Right = History)
# FIXED LINE BELOW: Added the number 2 inside columns
left_web_col, right_web_col = st.columns(2)

with left_web_col:
    st.subheader(" Live Fleet Positioning Map")
    # Generate Web Map Object using Folium
    m = folium.Map(location=[truck_lat, truck_lon], zoom_start=13, control_scale=True)
    folium.Marker(
        [truck_lat, truck_lon], 
        popup="Active Fleet Vehicle", 
        tooltip="Truck 01: Active",
        icon=folium.Icon(color="blue", icon="truck", prefix="fa")
    ).add_to(m)
    # Render the map directly on the web page
    st_folium(m, width="100%", height=450, returned_objects=[])

with right_web_col:
    st.subheader(" Live Database Audit Log")
    conn = sqlite3.connect('truck_web_logistics.db')
    df = pd.read_sql_query("SELECT barcode as 'Item ID', action as 'Status', timestamp as 'Logged Time' FROM asset_history ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("System idle. Scan a barcode to populate web database history logs.")
    else:
        # Displays data in a clean web spreadsheet style
        st.dataframe(df, use_container_width=True, height=450)
