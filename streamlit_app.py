import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
import os
import sys

# Import logic from main.py
import main as backend

# Page configuration
st.set_page_config(
    page_title="Autobot | Network Automation Engine",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Modern Blue Theme
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: #0c1221;
        background-image: 
            radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 50%);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #080d1a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Card-like styling for components */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Input fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #3b82f6;
        font-size: 2.5rem;
    }
    
    /* Success/Error badges */
    .status-active { color: #10b981; font-weight: bold; }
    .status-available { color: #3b82f6; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []
if 'selected_ips' not in st.session_state:
    st.session_state.selected_ips = []

# Sidebar Navigation
with st.sidebar:
    st.title("🤖 AUTOBOT")
    st.markdown("---")
    menu = st.radio(
        "Navigation",
        ["📊 Dashboard", "🔍 IP Scan", "🚀 Config Push", "🔑 Credentials"],
        index=0
    )
    st.markdown("---")
    st.info("Engine Online", icon="🟢")

# Helper: Load Credentials for dropdowns
creds_data = backend.load_credentials()
group_options = list(creds_data.keys())

# Views
if menu == "📊 Dashboard":
    st.title("Dashboard Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Scanned", len(st.session_state.scan_results))
    with col2:
        active_count = sum(1 for r in st.session_state.scan_results if r['status'] == 'Active')
        st.metric("Active IPs", active_count)
    with col3:
        available_count = sum(1 for r in st.session_state.scan_results if r['status'] == 'Available')
        st.metric("Available IPs", available_count)
    
    st.subheader("Recent Available IPs")
    if st.session_state.scan_results:
        available_df = pd.DataFrame([r for r in st.session_state.scan_results if r['status'] == 'Available'])
        if not available_df.empty:
            st.table(available_df[['ip', 'last_seen']].head(10))
        else:
            st.write("No available IPs found yet.")
    else:
        st.write("Please run a scan first.")

elif menu == "🔍 IP Scan":
    st.title("Network IP Scanner")
    
    with st.container():
        ip_range = st.text_input("IP Range / CIDR / List", placeholder="e.g. 172.27.14.0/24")
        if st.button("Start Scan", use_container_width=True):
            if ip_range:
                ips = backend.parse_ip_range(ip_range)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Mocking the background task for Streamlit synchronous behavior
                # In production, you might want to use st.empty() updates
                results = []
                for i, ip in enumerate(ips):
                    progress = int(((i + 1) / len(ips)) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Scanning {ip}...")
                    
                    # Call the core scan logic (we'll simulate the async call)
                    # For simplicity, we'll run a simplified version of backend.run_ip_scan
                    # In a real app, you'd want to handle the async loop properly
                    latency = backend.ping(ip, timeout=0.2)
                    is_active = latency is not None
                    ports = []
                    if is_active:
                        for p in [22, 80, 443]:
                            if backend.check_port(ip, p, timeout=0.1): ports.append(p)
                    
                    res = {
                        "ip": ip,
                        "status": "Active" if is_active else "Available",
                        "latency": f"{latency*1000:.2f}ms" if latency else "N/A",
                        "mac": "N/A",
                        "ports": ", ".join(map(str, ports)) if ports else "None",
                        "last_seen": datetime.now().strftime("%H:%M:%S")
                    }
                    results.append(res)
                
                st.session_state.scan_results = results
                st.success("Scan Completed!")
            else:
                st.error("Please enter an IP range.")

    if st.session_state.scan_results:
        st.subheader("Scan Results")
        df = pd.DataFrame(st.session_state.scan_results)
        
        # IP Multi-select via Checkbox column (using st.data_editor if available or simple check)
        st.write("Select IPs to configure:")
        available_ips = [r['ip'] for r in st.session_state.scan_results if r['status'] == 'Available']
        selected = st.multiselect("Available IPs", options=available_ips, default=st.session_state.selected_ips)
        st.session_state.selected_ips = selected
        
        st.dataframe(df, use_container_width=True)

elif menu == "🚀 Config Push":
    st.title("Automation Hub")
    
    col_l, col_r = st.columns([1, 1.2])
    
    with col_l:
        st.subheader("🎯 Target Definition")
        # Pre-fill from selected IPs
        target_ip = st.text_input("Target IP(s)", value=", ".join(st.session_state.selected_ips))
        
        use_group = st.checkbox("Use Credential Group")
        if use_group:
            selected_group = st.selectbox("Select Group", options=group_options)
            user = None
            pw = None
        else:
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            selected_group = None

    with col_r:
        st.subheader("📜 Configuration Template")
        commands = st.text_area("Commands", height=200, placeholder="set system host-name {{hostname}}")
        
        # Dynamic variable detection
        import re
        matches = re.findall(r"\{\{([^}]+)\}\}", commands)
        unique_vars = sorted(list(set(matches)))
        
        template_values = {}
        if unique_vars:
            st.markdown("---")
            st.write("Template Variables")
            cols = st.columns(2)
            for i, var in enumerate(unique_vars):
                template_values[var] = cols[i % 2].text_input(f"Value for {var}", key=f"var_{var}")

    st.markdown("---")
    if st.button("🚀 Preview & Deploy", use_container_width=True):
        if not target_ip or not commands:
            st.error("Please fill in Target IP and Commands.")
        else:
            # Substitute variables for preview
            final_config = commands
            for k, v in template_values.items():
                final_config = final_config.replace(f"{{{{{k}}}}}", v)
            
            st.session_state.preview_config = final_config
            st.session_state.target_ip_final = target_ip
            st.session_state.cred_info = {
                "user": user, "pw": pw, "group": selected_group
            }
            st.session_state.show_modal = True

    # Modal Simulation
    if st.session_state.get('show_modal'):
        with st.expander("👁️ Configuration Preview", expanded=True):
            st.code(st.session_state.preview_config)
            st.warning("Please review the generated configuration before committing.")
            
            c1, c2 = st.columns(2)
            if c1.button("❌ Cancel"):
                st.session_state.show_modal = False
                st.rerun()
                
            if c2.button("✅ Confirm & Commit"):
                # Call backend logic
                st.info(f"Initiating deployment to {st.session_state.target_ip_final}...")
                
                # Iterate through IPs if comma separated
                ips_to_push = [ip.strip() for ip in st.session_state.target_ip_final.split(",")]
                
                for ip in ips_to_push:
                    st.write(f"Connecting to {ip}...")
                    # Build request object
                    req = backend.ConfigPushRequest(
                        target_ip=ip,
                        username=st.session_state.cred_info['user'],
                        password=st.session_state.cred_info['pw'],
                        user_group=st.session_state.cred_info['group'],
                        commands=commands,
                        template_values=template_values
                    )
                    
                    # Run the async function in a sync environment
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(backend.push_config(req))
                    
                    if result['status'] == 'success':
                        st.success(f"Successfully configured {ip}")
                        st.text_area(f"Log for {ip}", value=result['log'], height=150)
                    else:
                        st.error(f"Failed to configure {ip}")
                        st.text_area(f"Error Log for {ip}", value=result['log'], height=150)
                
                st.session_state.show_modal = False

elif menu == "🔑 Credentials":
    st.title("User Groups & Credentials")
    
    with st.expander("➕ Add New Credential Group"):
        new_group = st.text_input("Group Name (e.g. CORE_SWITCH)")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Save Credentials"):
            if new_group and new_user and new_pass:
                creds = backend.load_credentials()
                creds[new_group] = {"username": new_user, "password": new_pass}
                backend.save_credentials(creds)
                st.success(f"Group {new_group} saved!")
                st.rerun()
    
    st.markdown("---")
    st.subheader("Saved Groups")
    if group_options:
        for group in group_options:
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{group}**")
            c2.write(f"User: {creds_data[group]['username']}")
            if c3.button("Delete", key=f"del_{group}"):
                del creds_data[group]
                backend.save_credentials(creds_data)
                st.rerun()
    else:
        st.write("No groups saved.")

st.sidebar.markdown("---")
st.sidebar.write("© 2026 Autobot Engine")
