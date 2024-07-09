import requests
import json
from web3 import Web3
import os
import csv
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

# Web3 setup
private_key = os.getenv('PRIVATE_KEY')
w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/bsc/20d05e2dff4538bfaf90396dc4715ec46ae9b90086bb3cb8f918e9d67a7ce19b'))

# Create an account object from the private key
account = Account.from_key(private_key)

# Load ABIs
with open('DlnSource.abi.json') as f:
    dln_source_abi = json.load(f)

with open('erc20.abi.json') as f:  # Load the ERC-20 ABI
    erc20_abi = json.load(f)

# Contract addresses
DLN_SOURCE_ADDRESS = "0xeF4fB24aD0916217251F553c0596F8Edc630EB66"
SRC_CHAIN_TOKEN_IN_ADDRESS = "0x2170Ed0880ac9A755fd29B2688956BD959F933F8"  # USDC on solana

# Create contract instances
dln_source_contract = w3.eth.contract(address=DLN_SOURCE_ADDRESS, abi=dln_source_abi)
spl_contract = w3.eth.contract(address=SRC_CHAIN_TOKEN_IN_ADDRESS, abi=erc20_abi)

# Function to get a quote
def get_quote(src_chain_id, src_chain_token_in, src_chain_token_in_amount, dst_chain_id, dst_chain_token_out, affiliate_fee_percent, prepend_operating_expenses):
    url = "https://api.dln.trade/v1.0/dln/order/quote"
    params = {
        "srcChainId": src_chain_id,
        "srcChainTokenIn": src_chain_token_in,
        "srcChainTokenInAmount": src_chain_token_in_amount,
        "dstChainId": dst_chain_id,
        "dstChainTokenOut": dst_chain_token_out,
        "dstChainTokenOutAmount": "auto",
        "affiliateFeePercent": affiliate_fee_percent,
        "prependOperatingExpenses": prepend_operating_expenses
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Function to create a transaction
def create_tx(src_chain_id, src_chain_token_in, src_chain_token_in_amount, dst_chain_id, dst_chain_token_out, inte, dst_chain_token_out_amount, dst_chain_token_out_recipient, src_chain_order_authority_address, affiliate_fee_percent, affiliate_fee_recipient, dst_chain_order_authority_address, prepend_operating_expenses):
    url = "https://api.dln.trade/v1.0/dln/order/create-tx"
    params = {
        "srcChainId": src_chain_id,
        "srcChainTokenIn": src_chain_token_in,
        "srcChainTokenInAmount": src_chain_token_in_amount,
        "dstChainId": dst_chain_id,
        "dstChainTokenOut": dst_chain_token_out,
        "dstChainTokenOutAmount": dst_chain_token_out_amount,
        "dstChainTokenOutRecipient": dst_chain_token_out_recipient,
        "srcChainOrderAuthorityAddress": src_chain_order_authority_address,
        "affiliateFeePercent": affiliate_fee_percent,
        "affiliateFeeRecipient": affiliate_fee_recipient,
        "dstChainOrderAuthorityAddress": dst_chain_order_authority_address,
        "prependOperatingExpenses": prepend_operating_expenses,
        "refferalCode": inte
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Example usage
src_chain_id = 42161  # ARB
src_chain_token_in = SRC_CHAIN_TOKEN_IN_ADDRESS  # USDC on Arbitrum
src_chain_token_in_amount = 3500000000000  # Use "auto" as specified in the URL
dst_chain_id = 56  # BNB
dst_chain_token_out = "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d"  # USDC on BNB
dst_chain_token_out_amount = "auto"  # Amount in smallest unit
dst_chain_token_out_recipient = "0xef772390c8aDD25302be26Fb92edb7F5dE214480"
src_chain_order_authority_address = "0x09fe3a3EA67eD2fEceFa9Af22380e53f0F580614"
affiliate_fee_percent = 0.01
affiliate_fee_recipient = "0x09fe3a3EA67eD2fEceFa9Af22380e53f0F580614"
dst_chain_order_authority_address = "0xef772390c8aDD25302be26Fb92edb7F5dE214480"
prepend_operating_expenses = True # Set to False as specified in the URL
inte = "15434"

try:
    quote = get_quote(src_chain_id, src_chain_token_in, src_chain_token_in_amount, dst_chain_id, dst_chain_token_out, affiliate_fee_percent, prepend_operating_expenses)
    print(json.dumps(quote, indent=4))  # Pretty-print the JSON response
    
    tx = create_tx(src_chain_id, src_chain_token_in, src_chain_token_in_amount, dst_chain_id, dst_chain_token_out, dst_chain_token_out_amount, dst_chain_token_out_recipient, src_chain_order_authority_address, affiliate_fee_percent, affiliate_fee_recipient, dst_chain_order_authority_address, prepend_operating_expenses)
    print(json.dumps(tx, indent=4))  # Pretty-print the JSON response
    
    # Extract necessary fields from the tx dictionary
    quotetx = quote.get('tx', {})
    nested_tx = tx.get('tx', {})
    allowance_target = quotetx.get('allowanceTarget')
    allowance_value = quotetx.get('allowanceValue')
    to = nested_tx.get('to')
    data = nested_tx.get('data')
    value = nested_tx.get('value')

    # Ensure the required fields are not None
    if allowance_target is None or allowance_value is None or to is None or data is None or value is None:
        raise ValueError("Missing required transaction fields: 'allowanceTarget', 'allowanceValue', 'to', 'data', or 'value'")

    # Convert allowance_value to integer
    allowance_value = int(allowance_value)

    # Check the current allowance
    current_allowance = spl_contract.functions.allowance(account.address, allowance_target).call()
    print(f"Current allowance: {current_allowance}")

    # Estimate gas for the approve
    gas_estimate = spl_contract.functions.approve(
        allowance_target, 
        allowance_value
    ).estimate_gas({
        'from': account.address
    })

    # Approve the smart contract to spend the tokens
    approve_txn = spl_contract.functions.approve(
        allowance_target,  # The smart contract address specified in the tx.allowanceTarget field
        allowance_value  # The amount specified as the tx.allowanceValue property
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': gas_estimate,
        'gasPrice': w3.eth.gas_price
    })

    signed_approve_txn = w3.eth.account.sign_transaction(approve_txn, private_key)
    w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)

    # Wait for the approval transaction to be mined
    w3.eth.wait_for_transaction_receipt(signed_approve_txn.hash)

    # Check the updated allowance
    updated_allowance = spl_contract.functions.allowance(account.address, allowance_target).call()
    print(f"Updated allowance: {updated_allowance}")

    # Estimate gas for the main transaction
    gas_estimate = w3.eth.estimate_gas({
        'to': to,
        'data': data,
        'value': int(value),
        'from': account.address
    })

    # Create the new transaction dictionary
    transaction = {
        'to': to,
        'data': data,
        'value': int(value),  # Ensure value is an integer
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': gas_estimate,
        'maxPriorityFeePerGas': w3.eth.gas_price,
        'maxFeePerGas': w3.eth.gas_price + w3.eth.gas_price,
        'chainId': src_chain_id
    }

    # Sign the transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)

    # Send the transaction
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Print the transaction hash
    # After sending the transaction, write the tx_hash to a CSV file
    csv_file = 'tx_hashes.csv'
    txn_hash_hex = txn_hash.hex()

    # Check if the CSV file exists
    file_exists = os.path.isfile(csv_file)

    # Write the transaction hash to the CSV file
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write the header if the file does not exist
            writer.writerow(['tx_hash'])
        writer.writerow([txn_hash_hex])


except Exception as e:
    print(f"An error occurred: {e}")