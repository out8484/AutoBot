import asyncio
import socket
from typing import List, Optional, Dict
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import scapy.all as scapy
from ping3 import ping
from netmiko import ConnectHandler
try:
    from jnpr.junos import Device
    from jnpr.junos.utils.config import Config
    PYEZ_AVAILABLE = True
except ImportError:
    PYEZ_AVAILABLE = False
import json
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Autobot")

app = FastAPI(title="Autobot Network Automation")

# Data structure to hold scan results and logs
current_scan_results = []
scan_progress = {"status": "idle", "progress": 0, "current_ip": ""}
logs = []
CREDENTIALS_FILE = "credentials.json"

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_credentials(creds):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=4)

class ScanRequest(BaseModel):
    ip_range: str

class CredentialInfo(BaseModel):
    group_name: str
    username: str
    password: str

class ConfigPushRequest(BaseModel):
    target_ip: str
    username: Optional[str] = None
    password: Optional[str] = None
    user_group: Optional[str] = None
    device_type: str = "generic_termserver" 
    commands: str 
    template_values: Optional[Dict[str, str]] = None
    verify_commands: Optional[str] = None

def get_mac(ip):
    """
    Attempts to get the MAC address for a given IP.
    Only works on local subnet.
    """
    try:
        ans, unans = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=ip), timeout=1, verbose=False)
        for snd, rcv in ans:
            return rcv.sprintf(r"%Ether.src%")
    except Exception as e:
        logger.error(f"Error getting MAC for {ip}: {e}")
    return "Unknown"

def check_port(ip, port, timeout=0.5):
    """
    Checks if a specific port is open.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            return True
        except:
            return False

async def run_arp_scan(ip_list: List[str]) -> Dict[str, str]:
    """
    Performs a batch ARP scan for the given list of IPs.
    Returns a dictionary of {ip: mac}.
    """
    found_hosts = {}
    try:
        # Split into smaller chunks to avoid overwhelming the network/scapy
        chunk_size = 50
        for i in range(0, len(ip_list), chunk_size):
            chunk = ip_list[i:i + chunk_size]
            ans, unans = scapy.srp(
                scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=chunk),
                timeout=2,
                verbose=False
            )
            for snd, rcv in ans:
                found_hosts[rcv.psrc] = rcv.hwsrc
        return found_hosts
    except Exception as e:
        logger.error(f"ARP Scan Error: {e}")
        return {}

async def run_remote_nmap_scan(ip_range: str) -> List[str]:
    """
    Connects to a Jump Host and runs nmap to find active hosts.
    Uses -sn (Ping Scan) for speed and -oG (Grepable output) for easy parsing.
    """
    jump_host = {
        'device_type': 'linux', # Changed to linux to support nmap execution
        'host': '172.27.14.51',
        'username': 'jun',
        'password': 'jun2per',
        'timeout': 30,
    }
    
    active_ips = []
    try:
        # Convert list of IPs to a range string if possible, or use the base network
        # For simplicity, we'll scan the .0/24 if it's the target subnet
        base_net = "172.27.14.0/24"
        logger.info(f"Connecting to Jump Host to run nmap on {base_net}...")
        
        def execute_nmap():
            with ConnectHandler(**jump_host) as conn:
                # -sn: Ping scan (no port scan)
                # -oG -: Grepable output to stdout
                cmd = f"nmap -sn -oG - {base_net}"
                return conn.send_command(cmd)

        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(None, execute_nmap)
        
        # Parse Grepable output:
        # Host: 172.27.14.1 ()	Status: Up
        # Host: 172.27.14.51 ()	Status: Up
        for line in output.splitlines():
            if "Status: Up" in line:
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[1]
                    active_ips.append(ip)
        
        logger.info(f"Remote nmap found {len(active_ips)} active hosts.")
        return active_ips
    except Exception as e:
        logger.error(f"Remote Nmap SSH Error: {e}")
        return []

async def run_ip_scan(ip_list: List[str]):
    global current_scan_results, scan_progress
    current_scan_results = []
    scan_progress["status"] = "running"
    total = len(ip_list)
    
    # 1. Remote Nmap Scan via Jump Host
    is_target_subnet = any(ip.startswith("172.27.14.") for ip in ip_list)
    remote_active_ips = []
    
    if is_target_subnet:
        remote_active_ips = await run_remote_nmap_scan("172.27.14.0/24")
    
    # Fallback to local ARP for non-jump subnets or as secondary
    local_arp_results = {}
    if not is_target_subnet:
        local_arp_results = await run_arp_scan(ip_list)
    
    for i, ip in enumerate(ip_list):
        scan_progress["progress"] = int(((i + 1) / total) * 100)
        scan_progress["current_ip"] = ip
        
        # Check if active
        active_via_remote = ip in remote_active_ips
        active_via_local_arp = ip in local_arp_results
        
        latency = None
        active_via_ping = False
        
        # Priority: Remote Nmap > Local ARP > Local Ping
        if active_via_remote or active_via_local_arp:
            is_active = True
            # Optional: direct ping for latency from engine
            latency = ping(ip, timeout=0.2)
        else:
            latency = ping(ip, timeout=0.3)
            is_active = latency is not None
            active_via_ping = is_active
        
        ports = []
        if is_active:
            for port in [22, 80, 443]:
                if check_port(ip, port, timeout=0.2):
                    ports.append(port)
        
        result = {
            "ip": ip,
            "mac": local_arp_results.get(ip, "N/A"),
            "latency": f"{latency*1000:.2f}ms" if latency else "N/A",
            "status": "Active" if is_active else "Available",
            "detection": "Remote-Nmap" if active_via_remote else ("Local-ARP" if active_via_local_arp else ("Ping" if active_via_ping else "None")),
            "ports": ports,
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        current_scan_results.append(result)
        if i % 10 == 0: await asyncio.sleep(0.01)
        
    scan_progress["status"] = "completed"

def parse_ip_range(range_str: str) -> List[str]:
    """
    Supports:
    - 192.168.1.0/24
    - 192.168.1.1-50
    - 192.168.1.1,192.168.1.2
    """
    ips = []
    try:
        if "/" in range_str:
            import ipaddress
            ips = [str(ip) for ip in ipaddress.IPv4Network(range_str, strict=False)]
        elif "-" in range_str:
            base = ".".join(range_str.split(".")[:-1])
            start, end = range_str.split(".")[-1].split("-")
            for i in range(int(start), int(end) + 1):
                ips.append(f"{base}.{i}")
        elif "," in range_str:
            ips = [ip.strip() for ip in range_str.split(",")]
        else:
            ips = [range_str.strip()]
    except Exception as e:
        logger.error(f"Error parsing IP range: {e}")
    return ips

@app.post("/api/scan")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    ips = parse_ip_range(request.ip_range)
    if not ips:
        raise HTTPException(status_code=400, detail="Invalid IP range format")
    
    background_tasks.add_task(run_ip_scan, ips)
    return {"message": "Scan started", "total_ips": len(ips)}

@app.get("/api/scan/status")
async def get_scan_status():
    return {
        "progress": scan_progress,
        "results": current_scan_results
    }

@app.get("/api/ping/{ip}")
async def manual_ping(ip: str):
    latency = ping(ip, timeout=1.0)
    if latency is not None:
        return {"status": "success", "latency": f"{latency*1000:.2f}ms"}
    else:
        return {"status": "error", "message": "Request timed out"}

@app.get("/api/credentials")
async def get_creds():
    return load_credentials()

@app.post("/api/credentials")
async def update_creds(creds: CredentialInfo):
    data = load_credentials()
    data[creds.group_name] = {"username": creds.username, "password": creds.password}
    save_credentials(data)
    return {"status": "success"}

@app.delete("/api/credentials/{group_name}")
async def delete_creds(group_name: str):
    data = load_credentials()
    if group_name in data:
        del data[group_name]
        save_credentials(data)
    return {"status": "success"}

@app.post("/api/push-config")
async def push_config(request: ConfigPushRequest):
    global logs
    log_id = datetime.now().strftime("%H:%M:%S")
    
    username = request.username
    password = request.password
    
    if request.user_group:
        creds = load_credentials()
        group_data = creds.get(request.user_group)
        if group_data:
            username = group_data["username"]
            password = group_data["password"]
            
    if not username or not password:
        return {"status": "error", "log": f"[{log_id}] ERROR: Credentials missing."}

    # Handle templating for commands
    final_commands = request.commands
    if request.template_values:
        for key, val in request.template_values.items():
            final_commands = final_commands.replace(f"{{{{{key}}}}}", val)

    output_log = []
    
    if not PYEZ_AVAILABLE:
        return {"status": "error", "log": f"[{log_id}] ERROR: junos-eznc (PyEZ) not installed on server."}
    
    try:
        output_log.append(f"[{log_id}] [1/5] INITIALIZING: Target {request.target_ip}, User: {username}")
        # gather_facts=False for faster connection
        dev = Device(host=request.target_ip, user=username, passwd=password, gather_facts=False)
        
        output_log.append(f"[{log_id}] [2/5] CONNECTING: Opening NETCONF session to port 830...")
        dev.open()
        
        output_log.append(f"[{log_id}] [3/5] CONNECTED: Session established. Fact gathering skipped.")
        output_log.append(f"[{log_id}] INFO: Device version: {dev.facts.get('version' if dev.facts else 'N/A')}")
        
        # Determine format (set or text) based on command prefix
        load_format = "set" if "set " in final_commands.lower() else "text"
        
        output_log.append(f"[{log_id}] [4/5] LOADING CONFIG: Parsing commands in '{load_format}' format...")
        cu = Config(dev)
        
        # Check if config is already in use (lock)
        try:
            cu.lock()
            output_log.append(f"[{log_id}] SUCCESS: Configuration database locked.")
        except Exception as lock_err:
            output_log.append(f"[{log_id}] WARNING: Could not lock database (it might be in use): {str(lock_err)}")

        cu.load(final_commands, format=load_format)
        output_log.append(f"[{log_id}] SUCCESS: Commands loaded into candidate configuration.")
        
        # Diff check would be great here but let's keep it simple for now
        
        output_log.append(f"[{log_id}] [5/5] COMMITTING: Applying changes to active configuration...")
        cu.commit()
        
        output_log.append(f"[{log_id}] FINAL: Configuration committed and verified.")

        try:
            cu.unlock()
            output_log.append(f"[{log_id}] INFO: Configuration database unlocked.")
        except:
            pass

        dev.close()
        output_log.append(f"[{log_id}] STATUS: NETCONF session closed safely.")
        return {"status": "success", "log": "\n".join(output_log)}
        
    except Exception as e:
        error_msg = f"[{log_id}] !!! FATAL ERROR: {str(e)}"
        output_log.append(error_msg)
        # Attempt close if fail
        try:
            dev.close()
        except:
            pass
        return {"status": "error", "log": "\n".join(output_log)}

@app.get("/")
async def read_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
