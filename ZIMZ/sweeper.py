from web3 import Web3
import time
import json
import os

LOG_FILE = "log.json"

def save_log(message):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": message
    }

    # Check if log file exists; if not, create it
    # if not os.path.exists(LOG_FILE):
    #     with open(LOG_FILE, "w") as file:
    #         json.dump([], file)

    # Read existing logs
    try:
        with open(LOG_FILE, "r") as file:
            logs = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        logs = []

    # Append new log
    logs.append(log_entry)

    # Save back to file
    with open(LOG_FILE, "w") as file:
        json.dump(logs, file, indent=4)

def get_logs():
    try:
        with open(LOG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


class SweeperBot:
    def __init__(self):
        self.running = False
        self.private_key = None
        self.monitor_address = None
        self.destination_address = None
        self.w3 = None

    def update_inputs(self, private_key, monitor_address, destination_address, websocket_url):
        self.private_key = private_key
        self.monitor_address = Web3.to_checksum_address(monitor_address)
        self.destination_address = Web3.to_checksum_address(destination_address)
        self.w3 = Web3(Web3.LegacyWebSocketProvider('wss://arbitrum-mainnet.infura.io/ws/v3/bed3b1f4d56446d2b871d74cbc88930f'))

        if not self.w3.is_connected():
            raise Exception("Failed to connect to the Ethereum node")

    def sweep_eth(self):
        balance = self.w3.eth.get_balance(self.monitor_address)
        gas_price = self.w3.eth.gas_price * 2
        gas_limit = 350000
        total_cost = gas_limit * gas_price

        save_log(f"Total cost: {total_cost}  Balance: {balance}")

        if balance > total_cost:
            nonce = self.w3.eth.get_transaction_count(self.monitor_address)
            tx = {
                'nonce': nonce,
                'to': self.destination_address,
                'value': balance - total_cost,
                'gas': gas_limit,
                'gasPrice': gas_price
            }

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)

            try:
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                save_log(f"Transaction sent with hash: {tx_hash.hex()}")
            except Exception as e:
                save_log(f"Error sending transaction: {e}")
        else:
            save_log("Insufficient funds to cover transaction and gas fees")

    def run(self):
        self.running = True
        while self.running:
            self.sweep_eth()
            time.sleep(0.25)

    def stop(self):
        self.running = False
        print("Sweeper bot stopped")

sweeper_instance = SweeperBot()
