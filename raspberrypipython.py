import time
from web3 import Web3

# Connect to Ganache running on your laptop over the local network
GANACHE_URL = "http://HOST_LAPTOP_IP:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    print("[ERROR] Cannot connect to Ganache RPC!")
    exit()

print("[SUCCESS] Pi connected to Ganache testnet!")

# Device credentials (Account 0 from Ganache GUI)
SENDER_ADDRESS = "0xbd022f398134fDAabC3Ef3081847B48b89CCdb4"
PRIVATE_KEY = "0xe0f5c1f7b2b06992264236d0a8da3bc4fb5e2cd160faef7dc4eaf116983fb5a1"
TARGET_ADDRESS = "0xf19316e0132b92f037d1aee934fabbb45319fca4"

def trigger_onchain_alert(threat_type):
    print(f"\n[ALERT] Threat Detected: {threat_type}!")
    print("[WEB3] Signing and sending immutable event payload...")

    nonce = w3.eth.get_transaction_count(SENDER_ADDRESS)
    tx = {
        'nonce': nonce,
        'to': TARGET_ADDRESS,
        'value': w3.to_wei(0.01, 'ether'),
        'gas': 200000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'chainId': 5777
    }

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[SUCCESS] Threat Logged On-Chain! Tx Hash: {w3.to_hex(tx_hash)}")

# Simulated sensor loop (Replace with GPIO / physical pin reads if using hardware)
if __name__ == "__main__":
    print("\n--- Raspberry Pi Active Threat Monitoring Node ---")
    try:
        while True:
            # Simulated trigger condition (e.g., reading a physical button or sensor)
            val = input("\nPress ENTER to simulate Pi Tamper / Threat Event (or 'q' to quit): ")
            if val.lower() == 'q':
                break
            trigger_onchain_alert("PHYSICAL_TAMPER_DETECTED")
    except KeyboardInterrupt:
        print("\nShutting down Pi Agent...")
