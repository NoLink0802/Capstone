import hashlib
import time
from web3 import Web3

# Connect directly to local Ganache RPC
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

SENDER = "0xbd022f398134fDAabC3Ef3081847B48b89CCdb4"
PRIVATE_KEY = "0xe0f5c1f7b2b06992264236d0a8da3bc4fb5e2cd160faef7dc4eaf116983fb5a1"
TARGET = "0xf19316e0132b92f037d1aee934fabbb45319fca4"
DUMMY_FILE = "virtual_sensor.py"

def get_file_hash():
    sha256 = hashlib.sha256()
    with open(DUMMY_FILE, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def log_hash_to_blockchain(status, file_hash):
    payload = f"NODE:VIRTUAL_PI|STATUS:{status}|HASH:{file_hash}"
    hex_data = w3.to_hex(text=payload)
    
    nonce = w3.eth.get_transaction_count(SENDER, 'pending')
    tx = {
        'nonce': nonce,
        'to': TARGET,
        'value': w3.to_wei(0.001, 'ether'),
        'gas': 200000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'data': hex_data,
        'chainId': 5777
    }
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f" -> Broadcasted Hash to Ganache! Tx: {w3.to_hex(tx_hash)}")

# 1. Initialize clean virtual sensor file
with open(DUMMY_FILE, "w") as f:
    f.write("def read_temperature(): return 22.5")

clean_hash = get_file_hash()
print("\n==================================================")
print("  VIRTUAL IOT EDGE NODE (Simulated Raspberry Pi)  ")
print("==================================================")
print(f"\n[STEP 1] Initializing Clean Firmware...")
print(f" Baseline SHA-256 Hash: {clean_hash}")
log_hash_to_blockchain("CLEAN_BASELINE", clean_hash)

input("\n[PRESS ENTER] Inject Simulated Malware into Virtual Node...")

# 2. Inject unauthorized modification
with open(DUMMY_FILE, "a") as f:
    f.write("\n# MALWARE_INJECTED: send_data_to_attacker_ip()")

infected_hash = get_file_hash()
print(f"\n[STEP 2] Firmware Tampered / Malware Injected!")
print(f" Infected SHA-256 Hash: {infected_hash}")
log_hash_to_blockchain("INFECTED_TAMPER", infected_hash)

print("\n[SUMMARY]")
print(f" Hash Match: {clean_hash == infected_hash}")
print(" Status: Mismatch detected! Immutable proof anchored on-chain.\n")
