    with st.form("barcode_scan_form", clear_on_submit=True):
        input_truck_id = st.text_input("Truck ID / Vehicle Name", placeholder="Enter your actual Truck plate/ID")
        input_barcode = st.text_input("Barcode Data", placeholder="Click here and scan active item barcode")
        input_status = st.selectbox("Update Trip Status", ["Picked Up (At Origin)", "Delivered (At Destination)"])
        
        submit_button = st.form_submit_button("💾 SAVE ROUTE SCAN TO DATABASE")
        
        if submit_button:
            if input_truck_id and input_barcode and supabase:
                with st.spinner("Resolving coordinate data into exact physical address..."):
                    resolved_address = get_readable_address(sim_lat, sim_lon)
                
                try:
                    match_res = supabase.table("fleet_scans").select("*").eq("truck_id", input_truck_id).eq("barcode", input_barcode).execute()
                    existing_record = match_res.data[0] if (match_res.data and len(match_res.data) > 0) else None
                    
                    if "Picked Up" in input_status:
                        record_payload = {
                            "truck_id": input_truck_id,
                            "barcode": input_barcode,
                            "status": "In Transit",
                            "pickup_location": resolved_address,
                            "delivery_location": "Pending Delivery",
                            "p_lat": sim_lat,
                            "p_lon": sim_lon,
                            "d_lat": None,
                            "d_lon": None
                        }
                    else:
                        if existing_record:
                            record_payload = {
                                "id": existing_record.get("id"),
                                "truck_id": input_truck_id,
                                "barcode": input_barcode,
                                "status": "Delivered",
                                "pickup_location": existing_record.get("pickup_location"),
                                "delivery_location": resolved_address,
                                "p_lat": existing_record.get("p_lat"),
                                "p_lon": existing_record.get("p_lon"),
                                "d_lat": sim_lat,
                                "d_lon": sim_lon
                            }
                        else:
                            record_payload = {
                                "truck_id": input_truck_id,
                                "barcode": input_barcode,
                                "status": "Delivered (No Match)",
                                "pickup_location": "Unknown Origin",
                                "delivery_location": resolved_address,
                                "p_lat": None,
                                "p_lon": None,
                                "d_lat": sim_lat,
                                "d_lon": sim_lon
                            }
                    
                    supabase.table("fleet_scans").upsert(record_payload).execute()
                    st.success("Database entry synced successfully!")
                    st.rerun()
                except Exception as db_err:
                    st.error(f"Failed to synchronize records to cloud cluster database: {db_err}")
            else:
                st.error("Validation Error: Check missing fields or database connectivity links.")

    # ----------------- 📑 3. DATA VIEW LAYER -----------------
    if scans_data:
        st.markdown("---")
        st.header("📊 Current System Log Entries")
        st.dataframe(pd.DataFrame(scans_data), use_container_width=True)

