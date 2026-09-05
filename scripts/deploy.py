"""
Compiles contracts/PostVerifier.sol and deploys it to Polygon Amoy
testnet (or specified RPC), using py-solc-x so no separate Hardhat/Node
toolchain is needed -- just Python.

Requires in your .env (or environment):
  AMOY_RPC_URL   -- e.g. https://polygon-amoy.drpc.org
  PRIVATE_KEY    -- your testnet wallet's private key (get testnet MATIC
                    from a Polygon Amoy faucet first, or this will fail
                    with "insufficient funds")

Run:
  python scripts/deploy.py

On success, prints the deployed contract address and writes
contract_abi.json (needed by chain.py to interact with the deployed
contract afterward). Copy the printed address into CONTRACT_ADDRESS in
your .env.
"""

import json
import os
import sys

from dotenv import load_dotenv
from solcx import compile_source, install_solc, set_solc_version
from web3 import Web3

load_dotenv()

SOLC_VERSION = "0.8.19"
CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "..", "contracts", "PostVerifier.sol")
ABI_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contract_abi.json")


def compile_contract():
    print(f"Installing solc v{SOLC_VERSION} via py-solc-x if needed...")
    try:
        install_solc(SOLC_VERSION)
        set_solc_version(SOLC_VERSION)
    except Exception as e:
        print(f"Note: solc install warning: {e}")

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    compiled = compile_source(source, output_values=["abi", "bin"])
    # Find PostVerifier interface
    contract_id, contract_interface = None, None
    for k, v in compiled.items():
        if "PostVerifier" in k:
            contract_id, contract_interface = k, v
            break
    if not contract_interface:
        contract_id, contract_interface = compiled.popitem()

    return contract_interface["abi"], contract_interface["bin"]


def deploy():
    rpc_url = os.environ.get("AMOY_RPC_URL") or os.environ.get("BLOCKCHAIN_RPC_URL")
    if not rpc_url:
        raise RuntimeError("Missing AMOY_RPC_URL in .env. Set AMOY_RPC_URL or BLOCKCHAIN_RPC_URL.")

    private_key = os.environ.get("PRIVATE_KEY") or os.environ.get("BLOCKCHAIN_PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("Missing PRIVATE_KEY in .env. Set PRIVATE_KEY or BLOCKCHAIN_PRIVATE_KEY.")

    if not private_key.startswith("0x"):
        private_key = "0x" + private_key

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to RPC at {rpc_url}")

    account = w3.eth.account.from_key(private_key)
    balance = w3.eth.get_balance(account.address)
    print(f"Deploying from account: {account.address}")
    print(f"Account balance: {w3.from_wei(balance, 'ether')} ETH/MATIC")

    if balance == 0:
        raise RuntimeError(
            f"Account {account.address} has 0 balance on this network. "
            f"Get testnet MATIC from a Polygon Amoy faucet before deploying."
        )

    abi, bytecode = compile_contract()
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    nonce = w3.eth.get_transaction_count(account.address)
    chain_id = w3.eth.chain_id
    gas_price = w3.eth.gas_price

    tx = Contract.constructor().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 500_000,
        "gasPrice": gas_price,
        "chainId": chain_id,
    })
    signed = account.sign_transaction(tx)
    raw_tx = getattr(signed, "raw_transaction", getattr(signed, "rawTransaction", None))
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    print(f"Deployment tx sent: {tx_hash.hex()} -- waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    address = receipt.contractAddress

    with open(ABI_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(abi, f, indent=2)

    print(f"Contract deployed successfully at: {address}")
    print(f"ABI saved to: {ABI_OUTPUT_PATH}")
    print(f"Add this to your .env: CONTRACT_ADDRESS={address}")
    return address, abi


if __name__ == "__main__":
    deploy()
