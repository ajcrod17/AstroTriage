import streamlit as st
import requests
import pandas as pd
import time

import os
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AstroLab AI - Triage Dashboard", layout="wide")

st.title("AstroLab AI Triage Dashboard")

col1, col2 = st.columns([8, 1])
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📝 New Intake", "📋 Request Tracking", "💬 Communication Details", "⚙️ Simulation Console"])

with tab1:
    st.header("New Maintenance Request")
    with st.form("intake_form"):
        channel = st.selectbox("Channel", ["WhatsApp", "Email", "Phone", "Portal"])
        message = st.text_area("Raw Message")
        submitted = st.form_submit_button("Submit Request")
        
        if submitted:
            with st.spinner("Processing through AI Triage..."):
                try:
                    res = requests.post(f"{API_URL}/intake", json={"message": message, "channel": channel})
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Request created! ID: {data['maintenance_request']['id']}")
                        st.info(f"AI Reasoning: {data['ai_reasoning']}")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Failed to connect to API: {str(e)}")

with tab2:
    st.header("Request Tracking")
    try:
        res = requests.get(f"{API_URL}/requests")
        if res.status_code == 200:
            reqs = res.json().get("requests", [])
            if reqs:
                df = pd.DataFrame(reqs)
                if 'building_name' in df.columns:
                    df['building_name'] = df['building_name'].fillna('None')
                if 'unit_identifier' in df.columns:
                    df['unit_identifier'] = df['unit_identifier'].fillna('None')
                    
                display_df = df[['id', 'channel', 'status', 'urgency', 'category', 'building_name', 'unit_identifier', 'needs_human_review', 'created_at']]
                
                def color_urgency(val):
                    color = '#ef4444' if val == 'EMERGENCY' else '#f59e0b' if val == 'HIGH' else '#10b981' if val == 'ROUTINE' else ''
                    return f'color: {color}; font-weight: bold;'
                    
                st.dataframe(display_df.style.map(color_urgency, subset=['urgency']), use_container_width=True)
            else:
                st.info("No maintenance requests found.")
        else:
            st.error("Failed to fetch requests from API.")
    except Exception as e:
        st.error(f"Failed to connect to API: {str(e)}")

with tab3:
    st.header("Communication Details")
    try:
        res = requests.get(f"{API_URL}/requests")
        reqs = res.json().get("requests", []) if res.status_code == 200 else []
        if reqs:
            req_ids = [r["id"] for r in reqs]
            selected_id = st.selectbox("Select Request ID", req_ids)
            
            if selected_id:
                details_res = requests.get(f"{API_URL}/requests/{selected_id}")
                if details_res.status_code == 200:
                    data = details_res.json()
                    request_data = data["request"]
                    logs = data["logs"]
                    wos = data["work_orders"]
                    
                    st.subheader(f"Request #{request_data['id']} Details")
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Status", request_data["status"])
                    col_b.metric("Urgency", request_data["urgency"])
                    col_c.metric("Category", request_data["category"])
                    
                    if request_data.get("needs_human_review"):
                        st.warning("⚠️ This request has been flagged for human review.")
                        
                    if wos:
                        st.success(f"✅ Work Order Scheduled: {wos[0]['scheduled_slot']}")
                        
                    st.markdown("### Communication Timeline")
                    for log in logs:
                        role = "user" if log["sender"] == "TENANT" else "assistant" if "SYSTEM" in log["sender"] else "human"
                        with st.chat_message(role):
                            st.markdown(f"**{log['sender']}** ({log['timestamp'][:16]}):")
                            st.write(log["message"])
                else:
                    st.error("Failed to fetch request details.")
        else:
            st.info("No requests available to view.")
    except Exception as e:
        st.error(f"Failed to connect to API: {str(e)}")

with tab4:
    st.header("Simulation Console")
    st.write("Use this console to simulate actions in the state machine without external integrations.")
    
    try:
        res = requests.get(f"{API_URL}/requests")
        reqs = res.json().get("requests", []) if res.status_code == 200 else []
        triaged_reqs = [r["id"] for r in reqs if r["status"] == "TRIAGED"]
        active_reqs = [r["id"] for r in reqs if r["status"] not in ["NEW", "COMPLETED", "SCHEDULED"] and not r.get("needs_human_review")]
        
        st.subheader("1. Dispatch to Vendor")
        if triaged_reqs:
            dispatch_id = st.selectbox("Select TRIAGED Request", triaged_reqs, key="dispatch_sel")
            if st.button("Trigger Dispatch"):
                with st.spinner("Dispatching..."):
                    d_res = requests.post(f"{API_URL}/simulate/dispatch/{dispatch_id}")
                    if d_res.status_code == 200:
                        st.success("Dispatched successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(d_res.text)
        else:
            st.info("No TRIAGED requests available to dispatch.")
            
        st.divider()
        st.subheader("2. Simulate Incoming Message")
        if active_reqs:
            msg_id = st.selectbox("Select Active Request", active_reqs, key="msg_sel")
            sender = st.selectbox("Sender", ["VENDOR", "TENANT"])
            sim_msg = st.text_area("Message Content")
            if st.button("Send Message"):
                with st.spinner("Processing message through AI Parser..."):
                    m_res = requests.post(f"{API_URL}/simulate/message", json={"request_id": msg_id, "sender": sender, "message": sim_msg})
                    if m_res.status_code == 200:
                        st.success("Message processed!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(m_res.text)
        else:
            st.info("No active requests in negotiation available.")
            
    except Exception as e:
        st.error(f"Failed to connect to API: {str(e)}")
