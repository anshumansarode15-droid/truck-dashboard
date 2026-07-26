@st.fragment(run_every="10s")
def show_live_map(data_source):
    try:
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
                
                # Check for Pickup coordinates
                if pd.notna(row.get('p_lat')) and pd.notna(row.get('p_lon')) and row['p_lat'] is not None:
                    folium.Marker(
                        location=[row['p_lat'], row['p_lon']],
                        popup=f"<b>Truck: {truck_plate}</b><br>Driver Mob: {mob}<br>Origin: {row.get('pickup_location', '')}",
                        tooltip=f"🚚 {truck_plate}",
                        icon=folium.Icon(color="blue", icon="play", prefix="fa")
                    ).add_to(base_map)
                
                # Check for Delivery coordinates
                if pd.notna(row.get('d_lat')) and pd.notna(row.get('d_lon')) and row['d_lat'] is not None:
                    folium.Marker(
                        location=[row['d_lat'], row['d_lon']],
                        popup=f"<b>Truck: {truck_plate}</b><br>Driver Mob: {mob}<br>Destination: {row.get('delivery_location', '')}",
                        tooltip=f"✅ {truck_plate}",
                        icon=folium.Icon(color="green", icon="stop", prefix="fa")
                    ).add_to(base_map)
                
                # Draw route polyline between pickup and delivery
                if pd.notna(row.get('p_lat')) and pd.notna(row.get('d_lat')):
                    folium.PolyLine(
                        locations=[[row['p_lat'], row['p_lon']], [row['d_lat'], row['d_lon']]],
                        color="#ff4b5c",
                        weight=4,
                        opacity=0.8
                    ).add_to(base_map)  # <-- Fixed closing parenthesis and added to base_map

        # Render the map in Streamlit
        st_folium(base_map, width=700, height=500)

    except Exception as e:
        st.error(f"Error rendering map layers: {e}")
