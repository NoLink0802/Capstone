from web3 import Web3
from eth_account import Account
import json
import os
import socket
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
account = Account.from_key(os.getenv("PRIVATE_KEY"))

with open("./build/contracts/DeviceIntegrityRegistry.json") as f:
    artifact = json.load(f)
    CONTRACT_ABI = artifact["abi"]

CONTRACT_ADDRESS = "0x45e171daF44a6dD648a6B7CBF491cA7dE4e5360d"
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def get_hostname_hash():
    hostname = socket.gethostname()
    return hashlib.sha256(hostname.encode()).digest()


def submit_integrity_check():
    device_hash = get_hostname_hash()
    
    #fake = "fake"
    #device_hash = hashlib.sha256(fake.encode()).digest()
    
    device_data = int(datetime.now().timestamp())
    
    print(f"Hostname: {socket.gethostname()}")
    print(f"Hash: {device_hash.hex()}")
    print(f"Timestamp: {device_data}")
    
    nonce = w3.eth.get_transaction_count(account.address)
    
    tx = contract.functions.submitIntegrityCheck(
        device_hash,
        device_data
    ).build_transaction({
        'from': account.address,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'chainId': w3.eth.chain_id
    })
    
    try:
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        print("Integrity check submitted")
    except Exception as e:
        print(f"Integrity check failed: {e}")
        print(f"TX Hash: {tx_hash.hex()}")


if __name__ == "__main__":
    print(f"Connected: {w3.is_connected()}\n")
    submit_integrity_check()

