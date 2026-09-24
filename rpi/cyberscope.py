import hashlib
import json
import os
import platform
import socket
import time
import psutil
import board
import adafruit_dht
from gpiozero import DigitalInputDevice
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Configuration
load_dotenv()

w3 = Web3(Web3.HTTPProvider("http://10.42.0.1:7545"))
account = Account.from_key(os.getenv("PRIVATE_KEY"))

with open("./DeviceIntegrityRegistry.json") as f:
    artifact = json.load(f)
    CONTRACT_ABI = artifact["abi"]

CONTRACT_ADDRESS = "0x2a362E8346FEAF0A7D5923fb0792aE11367b1080"
contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI
)

CHECK_INTERVAL_SECONDS = 3 # Routine check timer

# Light sensor, pin 7, gpio 4, bouncetime .3 is debounce so it doesnt spam the logs
light_sensor = DigitalInputDevice(4, pull_up=True, bounce_time=0.3)
# DHT11 Data Out on GPIO 24 (Physical Pin 18)
dht_device = adafruit_dht.DHT11(board.D24)
# tamper flag, once set to true, cannot be changed
chassis_tampered = False


def get_low_level_system_state() -> dict:
    system_data = {}

    # Base OS & Kernel architecture
    uname = platform.uname()
    system_data["os_system"] = uname.system
    system_data["os_release"] = uname.release
    system_data["os_version"] = uname.version
    system_data["machine"] = uname.machine

    # MAC addresses
    interfaces = {}
    for iface_name, addrs in psutil.net_if_addrs().items():
        interfaces[iface_name] = [
            addr.address
            for addr in addrs
            if addr.family == psutil.AF_LINK
            or str(addr.family) == "AddressFamily.AF_LINK"
        ]
    system_data["network_interfaces"] = interfaces

    # Hash configuration files
    critical_files = ["/etc/passwd", "/etc/resolv.conf", "/etc/hosts"]
    file_hashes = {}
    for filepath in critical_files:
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    file_hashes[filepath] = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                file_hashes[filepath] = "ERROR"

    system_data["critical_files"] = file_hashes

    # Light sensor state hash
    system_data["chassis_state"] = (
        "CHASSIS_BREACHED" if chassis_tampered else "CHASSIS_SECURE"
    )

    return system_data


def generate_state_hash(data_dict: dict) -> bytes:
    # Dictionairy into sorted JSON using determnistic sha256
    canonical_json = json.dumps(data_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical_json).digest()


def read_temperature_sensor() -> str:
    # Polls temp sensor, tried 3 times before returning fake value
    for _ in range(3):
        try:
            temp = dht_device.temperature
            humidity = dht_device.humidity
            if temp is not None:
                return f"\n  Temperature: {temp}°C\n  Humidity: {humidity}%"
        except RuntimeError:
            # 0.5s pause before trying again
            time.sleep(0.5)
        except Exception:
            break
    return "Temperature sensor error"  # Fallback if sensor not working


def submit_integrity_check(device_hash: str, device_data: str):
    nonce = w3.eth.get_transaction_count(account.address)

    tx = contract.functions.submitIntegrityCheck(
        device_hash, device_data
    ).build_transaction(
        {
            "from": account.address,
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
            "chainId": w3.eth.chain_id,
        }
    )

    try:
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        print("Integrity check submitted")
    except Exception as e:
        print(f"Integrity check failed: {e}")
        print(f"TX Hash: {tx_hash.hex()}")


def send_payload(trigger_reason: str):
    # Gets system state, hashes it, gets temp sensor reading, sends to the blockchain
    raw_system_state = get_low_level_system_state()
    device_hash = generate_state_hash(raw_system_state)
    sensor_reading = read_temperature_sensor()

    submit_integrity_check(device_hash, sensor_reading)

    timestamp = time.strftime("%X")
    print(
        f"[{timestamp}] Event: {trigger_reason}\nHash: {device_hash.hex()[:12]}...\nData: {sensor_reading}\nChassis: {raw_system_state['chassis_state']}"
    )


# Interrupt Handlers for light sensor
def on_light_detected():
    global chassis_tampered
    if not chassis_tampered:
        chassis_tampered = True


def on_light_cleared():
    global chassis_tampered
    chassis_tampered = False


light_sensor.when_activated = on_light_detected
light_sensor.when_deactivated = on_light_cleared


if __name__ == "__main__":
    print(f"CyberScope monitor active on {account.address[:6]}...{account.address[-4:]}")
    print(f"Connected: {w3.is_connected()}\n")
    send_payload("SYSTEM_STARTUP: Initial baseline hash")

    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)
        send_payload("PERIODIC_CHECK")
