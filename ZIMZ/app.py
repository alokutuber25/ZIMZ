from flask import Flask, render_template, request, jsonify
import threading
import json
import sweeper
from web3 import Web3
import solcx
solcx.install_solc('0.8.0')  # Install Solidity 0.8.0
solcx.set_solc_version('0.8.0')  # Set the version
from solcx import compile_source

ab
app = Flask(__name__)

sweeper_thread = None


ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/send_eth")
def send_eth_page():
    return render_template("send_eth.html")

@app.route("/send_eth_transaction", methods=["POST"])
def send_eth():

    try:
        private_key = request.form["private_key"]
        receiver = request.form["receiver"]
        eth_amount = float(request.form["eth_amount"])
        receiver = Web3.to_checksum_address(receiver)

        RPC_URL = "https://arbitrum-mainnet.infura.io/v3/bed3b1f4d56446d2b871d74cbc88930f"
        web3 = Web3(Web3.HTTPProvider(RPC_URL))

        if not web3.is_address(receiver):
            return jsonify({"status": "error", "message": "Invalid receiver address"})

        sender = web3.eth.account.from_key(private_key).address
        nonce = web3.eth.get_transaction_count(sender)

        value = web3.to_wei(eth_amount, "ether")
        gas_price = web3.eth.gas_price

        tx = {
            "to": receiver,
            "value": value,
            "gas": 350000,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": 42161,  # Arbitrum Mainnet Chain ID
        }

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return jsonify({"status": "success", "tx_hash": web3.to_hex(tx_hash)})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/send_token_page")
def send_token_page():
    return render_template("send_token.html")  # Load the HTML form

@app.route("/send_token", methods=["POST"])
def send_token():
    try:
        private_key = request.form["private_key"]
        receiver = request.form["receiver"]
        contract_address = request.form["contract_address"]
        token_amount = float(request.form["token_amount"])
        receiver = Web3.to_checksum_address(receiver)

        RPC_URL = "https://arbitrum-mainnet.infura.io/v3/bed3b1f4d56446d2b871d74cbc88930f"
        web3 = Web3(Web3.HTTPProvider(RPC_URL))

        # Validate receiver and contract address
        if not web3.is_address(receiver) or not web3.is_address(contract_address):
            return jsonify({"status": "error", "message": "Invalid receiver or contract address"})

        # Load ERC-20 contract ABI (Standard ABI)
        erc20_abi = json.loads('[{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"}]')

        # Get sender address from private key
        sender = web3.eth.account.from_key(private_key).address

        # Load contract
        contract = web3.eth.contract(address=contract_address, abi=erc20_abi)

        # Get token decimals
        decimals = contract.functions.decimals().call()
        amount_wei = int(token_amount * (10 ** decimals))

        # Get nonce
        nonce = web3.eth.get_transaction_count(sender)

        # Build transaction
        tx = contract.functions.transfer(receiver, amount_wei).build_transaction({
            "from": sender,
            "gas": 350000,  # Adjust based on token
            "gasPrice": web3.eth.gas_price,
            "nonce": nonce,
            "chainId": 42161,  # Arbitrum One
        })

        # Sign the transaction
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)

        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return jsonify({"status": "success", "tx_hash": web3.to_hex(tx_hash)})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/sweeper_bot")
def sweeper_bot():
    return render_template('sweeper_bot.html')

@app.route('/logs')
def logs():
    global monitor_address
    log_data = sweeper.get_logs()  # Fetch logs from sweeper.py
    return render_template('sweeperlog.html', logs=log_data, monitor_address=monitor_address)  

@app.route("/get_logs")
def get_logs_api():
    return jsonify(sweeper.get_logs())  # Return logs as JSON

@app.route("/start_sweeper", methods=["POST"])
def start_sweeper():
    global sweeper_thread, monitor_address
    data = request.json
    private_key = data.get("private_key")
    monitor_address = data.get("monitor_address")
    destination_address = data.get("destination_address")
    websocket_url = "wss://arbitrum-mainnet.infura.io/ws/v3/YOUR_INFURA_API"

    sweeper.sweeper_instance.update_inputs(private_key, monitor_address, destination_address, websocket_url)

    if sweeper_thread is None or not sweeper_thread.is_alive():
        sweeper_thread = threading.Thread(target=sweeper.sweeper_instance.run)
        sweeper_thread.daemon = True
        sweeper_thread.start()

    return jsonify({"message": "Sweeper bot started"})

@app.route("/stop_sweeper", methods=["POST"])
def stop_sweeper():
    sweeper.sweeper_instance.stop()
    # Clear log.json file after stopping
    with open("log.json", "w") as file:
        json.dump([], file)

    return jsonify({"message": "Sweeper bot stopped and logs cleared"})

contract_source = """
pragma solidity ^0.8.0;

contract SelfDestruct {
    address payable public receiver;
    
    constructor(address payable _receiver) payable {
        receiver = _receiver;
    }
    
    function selfDestruct() public {
        selfdestruct(receiver);
    }
}
"""

# Compile Contract
def compile_contract():
    compiled_sol = compile_source(contract_source)
    contract_id, contract_interface = compiled_sol.popitem()
    return contract_interface

# Deploy and Execute Self-Destruct Contract
def deploy_contract(private_key, receiver_address):
    WEB3_PROVIDER = "https://arbitrum-mainnet.infura.io/v3/bed3b1f4d56446d2b871d74cbc88930f"
    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
    account = w3.eth.account.from_key(private_key)
    contract_interface = compile_contract()
    contract = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    receiver_address = Web3.to_checksum_address(receiver_address)
    
    tx = contract.constructor(receiver_address).build_transaction({
        'from': account.address,
        'value': w3.to_wei(0.0001, 'ether'),  # Adjust ETH amount
        'gas': 1000000,
        'gasPrice': gas_price,
        'nonce': nonce
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract_address = tx_receipt.contractAddress
    deployed_contract = w3.eth.contract(address=contract_address, abi=contract_interface['abi'])
    
    tx = deployed_contract.functions.selfDestruct().build_transaction({
        'from': account.address,
        'gas': 1500000,
        'gasPrice': gas_price,
        'nonce': w3.eth.get_transaction_count(account.address)
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return w3.to_hex(tx_hash)

# Route for Self-Destruct Page
@app.route('/selfdestruct', methods=['GET', 'POST'])
def selfdestruct():
    message = None
    tx_hash = None

    if request.method == 'POST':
        private_key = request.form['private_key']
        receiver_address = request.form['receiver_address']
        
        try:
            tx_hash = deploy_contract(private_key, receiver_address)
            message = f"Transaction Successful! TX: <a href='https://arbiscan.io/tx/{tx_hash}' target='_blank'>{tx_hash}</a>"
        except Exception as e:
            message = f"Error: {str(e)}"

    return render_template('selfdestruct.html', message=message, tx_hash=tx_hash)

if __name__ == "__main__":
    app.run(debug=True)
