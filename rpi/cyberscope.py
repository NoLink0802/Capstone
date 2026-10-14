import hashlib
import json
import os
import platform
import socket
import stat
import struct
import sys
import tempfile
import time
import psutil
from gpiozero import DigitalInputDevice
import board
import adafruit_dht
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

# Configuration
RPC_URL = os.getenv("RPC_URL", "http://10.42.0.1:7545")
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key("0x537354dc84b00fa76b3aff660207f35b39be7daa38071e626e266859304e7c9d")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_PATH = os.path.join(BASE_DIR, "DeviceIntegrityRegistry.json")

with open(ARTIFACT_PATH, "r") as f:
    artifact = json.load(f)
    CONTRACT_ABI = artifact["abi"]

CONTRACT_ADDRESS = "0x45e171daF44a6dD648a6B7CBF491cA7dE4e5360d"
contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI
)

CHECK_INTERVAL_SECONDS = 5

# Sensors
light_sensor = DigitalInputDevice(4, pull_up=True, bounce_time=0.3)
dht_device = adafruit_dht.DHT11(board.D24)

# One-way tamper latch
chassis_tampered = False

CRITICAL_FILES = [
    "/etc/passwd",
    "/etc/resolv.conf",
    "/etc/hosts",
    "/etc/hostname",
    "/etc/security/access.conf",
    "/etc/networks",
]

def get_file_permissions(filepath: str) -> dict:
    try:
        st = os.stat(filepath)
        return {
            "mode": stat.filemode(st.st_mode),
            "octal": oct(st.st_mode & 0o7777),
            "uid": st.st_uid,
            "gid": st.st_gid,
        }
    except OSError:
        return {"error": "STAT_ERROR"}

def get_default_gateway() -> str:
    try:
        with open("/proc/net/route", "r") as f:
            next(f)  # skips header
            for line in f:
                fields = line.strip().split()
                if len(fields) >= 4 and fields[1] == "00000000" and int(fields[3], 16) & 0x2:
                    return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
    except Exception:
        pass
    return "NONE"

def get_low_level_system_state() -> dict:
    system_data = {}

    # OS & Kernel architecture
    uname = platform.uname()
    system_data["hostname"] = platform.node()
    system_data["os_system"] = uname.system
    system_data["os_release"] = uname.release
    system_data["os_version"] = uname.version
    system_data["machine"] = uname.machine
    system_data["temp_directory"] = tempfile.gettempdir()
    system_data["process_title"] = os.path.basename(sys.argv[0])

    # Hardware & Memory info
    system_data["total_physical_ram"] = psutil.virtual_memory().total
    system_data["total_swap_space"] = psutil.swap_memory().total
    system_data["cpu_logical_cores"] = os.cpu_count()

    # Board serial number
    board_serial = "UNKNOWN"
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Serial"):
                    board_serial = line.split(":")[1].strip()
                    break
    except Exception:
        pass
    system_data["board_serial"] = board_serial

    # CPU scaling limits & governor
    cpufreq = {}
    for node in ["scaling_max_freq", "scaling_min_freq", "scaling_governor"]:
        p = f"/sys/devices/system/cpu/cpu0/cpufreq/{node}"
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    cpufreq[node] = f.read().strip()
            except Exception:
                pass
    system_data["cpu_frequency_limits"] = cpufreq

    # Effective UID / GID
    system_data["effective_uid"] = os.geteuid()
    system_data["effective_gid"] = os.getegid()

    # Connected USB Devices
    usb_devs = []
    if os.path.exists("/sys/bus/usb/devices"):
        for dev in os.listdir("/sys/bus/usb/devices"):
            v_p = f"/sys/bus/usb/devices/{dev}/idVendor"
            p_p = f"/sys/bus/usb/devices/{dev}/idProduct"
            if os.path.exists(v_p) and os.path.exists(p_p):
                try:
                    with open(v_p) as vf, open(p_p) as pf:
                        usb_devs.append(f"{vf.read().strip()}:{pf.read().strip()}")
                except Exception:
                    pass
    usb_devs.sort()
    system_data["connected_usb"] = usb_devs

    # Ethernet carrier link
    eth_carrier = "0"
    if os.path.exists("/sys/class/net/eth0/carrier"):
        try:
            with open("/sys/class/net/eth0/carrier") as f:
                eth_carrier = f.read().strip()
        except Exception:
            pass
    system_data["ethernet_carrier_link"] = eth_carrier

    # HDMI port status
    hdmi_status = "NOT_DETECTED"
    if os.path.exists("/sys/class/drm"):
        for card in os.listdir("/sys/class/drm"):
            if "HDMI" in card:
                status_path = f"/sys/class/drm/{card}/status"
                if os.path.exists(status_path):
                    try:
                        with open(status_path) as f:
                            hdmi_status = f.read().strip()
                        break
                    except Exception:
                        pass
    system_data["hdmi_port"] = hdmi_status

    # Network Interfaces
    interfaces = {}
    for iface_name, addrs in psutil.net_if_addrs().items():
        iface_data = {"mac": [], "ipv4": []}
        for addr in addrs:
            if addr.family == psutil.AF_LINK or str(addr.family) == "AddressFamily.AF_LINK":
                iface_data["mac"].append(addr.address)
            elif addr.family == socket.AF_INET or str(addr.family) in ("AddressFamily.AF_INET", "2"):
                iface_data["ipv4"].append({"ip": addr.address, "netmask": addr.netmask})
        interfaces[iface_name] = iface_data
    system_data["network_interfaces"] = interfaces
    system_data["default_gateway"] = get_default_gateway()

    # Configuration files and permissions
    file_hashes = {}
    for filepath in CRITICAL_FILES:
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    file_hashes[filepath] = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                file_hashes[filepath] = "ERROR"
        else:
            file_hashes[filepath] = "NOT_FOUND"

    system_data["critical_files"] = file_hashes
    system_data["file_permissions"] = {
        f: get_file_permissions(f) for f in CRITICAL_FILES if os.path.exists(f)
    }

    # Sticky hardware latch
    system_data["chassis_state"] = "CHASSIS_BREACHED" if chassis_tampered else "CHASSIS_SECURE"

    return system_data

def generate_state_hash(data_dict: dict) -> bytes:
    canonical_json = json.dumps(data_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical_json).digest()

def read_temperature_sensor() -> str:
    for _ in range(3):
        try:
            temp = dht_device.temperature
            humidity = dht_device.humidity
            if temp is not None:
                return f"Temperature: {temp}°C | Humidity: {humidity}%"
        except RuntimeError:
            time.sleep(1.5)
        except Exception:
            break
    return "Temperature sensor error"

def submit_integrity_check(device_hash: bytes, device_data: str):
    tx_hash = None
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.submitIntegrityCheck(
            device_hash, device_data
        ).build_transaction(
            {
                "from": account.address,
                "gas": 250000,
                "gasPrice": w3.eth.gas_price,
                "nonce": nonce,
                "chainId": w3.eth.chain_id,
            }
        )

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        print("Integrity check submitted successfully.")
    except Exception as e:
        print(f"Integrity check failed: {e}")
        if tx_hash:
            print(f"TX Hash: {tx_hash.hex()}")

def send_payload(trigger_reason: str):
    raw_system_state = get_low_level_system_state()
    device_hash = generate_state_hash(raw_system_state)
    sensor_reading = read_temperature_sensor()

    submit_integrity_check(device_hash, sensor_reading)

    timestamp = time.strftime("%X")
    print(
        f"[{timestamp}] Event: {trigger_reason}\n"
        f"Hash: {device_hash.hex()[:16]}...\n"
        f"Data: {sensor_reading}\n"
        f"Chassis: {raw_system_state['chassis_state']}\n"
    )

def on_light_detected():
    global chassis_tampered
    if not chassis_tampered:
        chassis_tampered = True
        print(f"\n[{time.strftime('%X')}] *** PHYSICAL TAMPER DETECTED ***")
        send_payload("LIGHT_TAMPER_INTERRUPT")

def on_light_cleared():
    # Sticky latch persists; log re-seal without clearing the tamper state
    print(f"[{time.strftime('%X')}] Enclosure resealed (Tamper latch remains breached).")

light_sensor.when_activated = on_light_detected
light_sensor.when_deactivated = on_light_cleared

if __name__ == "__main__":
    print(f"CyberScope monitor active on: {account.address}")
    print(f"Connected to blockchain node: {w3.is_connected()}\n")

    send_payload("SYSTEM_STARTUP: Initial baseline hash")

    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)
        send_payload("PERIODIC_CHECK")
