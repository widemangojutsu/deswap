import requests
import json
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
import base64
import os
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey
from solders.keypair import Keypair as SoldersKeypair
from solders.instruction import Instruction, AccountMeta
from solders.message import MessageV0
from solders.rpc.responses import SendTransactionResp
from solders.hash import Hash
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from standardtx import StandardTxSender
import asyncio


# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Solana setup
solana_client = Client("https://solana-mainnet.g.alchemy.com/v2/KgpuMjqocuyieV47x-HcBYGyi8LrIFb8")
private_key = os.getenv('PRIVATE_KEY') # Your Solana private key
keypair = SoldersKeypair.from_base58_string(private_key)
public_key = keypair.pubkey

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
    quote = response.json()
    print(quote)
    return quote

def request_order_creation_transaction(quote):
    estimation = quote['estimation']
    src_chain_token_in = estimation['srcChainTokenIn']
    dst_chain_token_out = estimation['dstChainTokenOut']
    
    url = "https://api.dln.trade/v1.0/dln/order/create-tx"
    params = {
        "srcChainId": src_chain_token_in['chainId'],
        "srcChainTokenIn": src_chain_token_in['address'],
        "srcChainTokenInAmount": src_chain_token_in['amount'],
        "dstChainId": dst_chain_token_out['chainId'],
        "dstChainTokenOut": dst_chain_token_out['address'],
        "dstChainTokenOutAmount": dst_chain_token_out['recommendedAmount'],
        "dstChainTokenOutRecipient": '0xef772390c8aDD25302be26Fb92edb7F5dE214480',  # Adjust as needed
        "srcChainOrderAuthorityAddress": '8h3eQCUq4sfKraaSGgoQM2wt1kjCYq6BoaAkCrPt3waa',  # Adjust as needed
        "dstChainOrderAuthorityAddress": '0xef772390c8aDD25302be26Fb92edb7F5dE214480',  # Adjust as needed
        "affiliateFeePercent": quote.get('affiliateFeePercent', 0.1),
        "affiliateFeeRecipient": '8h3eQCUq4sfKraaSGgoQM2wt1kjCYq6BoaAkCrPt3waa',  # Adjust as needed
        "refferal_code": '15434'  # Adjust as needed
    }
    
    response = requests.get(url, params=params)
    order_creation_tx = response.json()
    print(order_creation_tx)
    return order_creation_tx

async def create_and_send_transaction(order_creation_tx):
    try:
        # Extract necessary fields from the tx dictionary
        tx_data = order_creation_tx.get('tx', {}).get('data')
        if tx_data is None:
            raise ValueError("Missing required transaction field: 'data'")

        # Decode the base64-encoded transaction data
        decoded_data = base64.b64decode(tx_data)

        # Deserialize the transaction
        versioned_tx = VersionedTransaction.from_bytes(decoded_data)

        # Initialize AsyncClient and StandardTxSender
        async_client = AsyncClient("https://solana-mainnet.g.alchemy.com/v2/KgpuMjqocuyieV47x-HcBYGyi8LrIFb8")
        tx_opts = TxOpts(skip_confirmation=False)
        tx_sender = StandardTxSender(async_client, tx_opts)

        # Sign the transaction
        solders_keypair = SoldersKeypair.from_bytes(bytes.fromhex(private_key))
        versioned_tx.sign([solders_keypair])

        # Send the transaction
        tx_sig_and_slot = await tx_sender.send(versioned_tx)
        print(f'Transaction signature: {tx_sig_and_slot.tx_sig}, Slot: {tx_sig_and_slot.slot}')

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
quote = get_quote(
    src_chain_id="7565164",  # Solana
    src_chain_token_in="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC on Solana
    src_chain_token_in_amount="1000000",  # Amount in smallest unit
    dst_chain_id=42161,  # Arbitrum
    dst_chain_token_out="0xaf88d065e77c8cc2239327c5edb3a432268e5831",  # USDC on Arbitrum
    affiliate_fee_percent=0.1,
    prepend_operating_expenses="true"
)

order_creation_tx = request_order_creation_transaction(quote)
asyncio.run(create_and_send_transaction(order_creation_tx))