import hashlib
import json
import os
import platform
import time
import psutil
from gpiozero import DigitalInputDevice
import board
import adafruit_dht

# Configuration
DEVICE_ID = "Raspberry Pi 01"
OUTPUT_FILE = "/home/capstone/cyberscope_payload.json"
CHECK_INTERVAL_SECONDS = 3  # Routine check timer

# Light sensor, pin 7, gpio 4, bouncetime .3 is debounce so it doesnt spam the logs
light_sensor = DigitalInputDevice(4, pull_up=True, bounce_time=0.3)
# DHT11 Data Out on GPIO 24 (Physical Pin 18)
dht_device = adafruit_dht.DHT11(board.D24)


# tamper flag, once set to true, cannot be changed
chassis_tampered = False


def get_low_level_system_state() -> dict:
    system_data = {}

    # 1.    Capture base OS & Kernel architecture
    uname = platform.uname()
    system_data["hostname"] = uname.node
    system_data["os_system"] = uname.system
    system_data["os_release"] = uname.release
    system_data["os_version"] = uname.version
    system_data["machine"] = uname.machine

    # 2. Capture MAC addresses
    interfaces = {}
    for iface_name, addrs in psutil.net_if_addrs().items():
        interfaces[iface_name] = [
            addr.address
            for addr in addrs
            if addr.family == psutil.AF_LINK or str(addr.family) == "AddressFamily.AF_LINK"
        ]
    system_data["network_interfaces"] = interfaces

    # 3. Hash configuration files
    critical_files = ["/etc/passwd", "/etc/resolv.conf", "/etc/hosts", "/etc/hostname"]
    file_hashes = {}
    for filepath in critical_files:
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    file_hashes[filepath] = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                file_hashes[filepath] = "ERROR"
    
    system_data["critical_files"] = file_hashes

    # 4. Light sensor state hash
    system_data["chassis_state"] = "CHASSIS_BREACHED" if chassis_tampered else "CHASSIS_SECURE"

    return system_data

def generate_state_hash(data_dict: dict) -> str:
    # Dictionairy into sorted JSON using determnistic sha256
    canonical_json = json.dumps(data_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical_json).hexdigest()


def read_temperature_sensor() -> str:
    # Polls temp sensor, tried 3 times before returning fake value
    for _ in range(3):
        try:
            temp = dht_device.temperature
            if temp is not None:
                return f"{temp}°C"
        except RuntimeError:
            # 0.5s pause before trying again
            time.sleep(0.5)
        except Exception:
            break
    return None  # Fallback temp if sensor not working, CHanged to NONE to indicate failure to read


def emit_payload(trigger_reason: str):
    #Gets system state, hashes it, gets temp sensor reading, puts it into a json friendly dict and writes it to a json file
    raw_system_state = get_low_level_system_state()
    device_hash = generate_state_hash(raw_system_state)
    sensor_reading = read_temperature_sensor()

    payload = {
        "Device ID": DEVICE_ID,
        "Device hash": device_hash,
        "Sensor Data": sensor_reading,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(payload, f, indent=4)

    timestamp = time.strftime("%X")
    print(f"[{timestamp}] Event: {trigger_reason} | Hash: {device_hash[:12]}... | Temp: {sensor_reading} | Chassis: {raw_system_state['chassis_state']}")


# Interrupt Handlers for light sensor
def on_light_detected():
    global chassis_tampered
    if not chassis_tampered:
        chassis_tampered = True
        emit_payload("Light breach detected")


def on_light_cleared():
    timestamp = time.strftime("%X")
    print(f"[{timestamp}] Enclosure Resealed (Device Still Tampered with)")


light_sensor.when_activated = on_light_detected
light_sensor.when_deactivated = on_light_cleared


if __name__ == "__main__":
    print(f"CyberScope monitor active on {DEVICE_ID} (User: capstone)...")
    emit_payload("SYSTEM_STARTUP: Initial baseline hash")

    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)
        emit_payload("PERIODIC_CHECK")
