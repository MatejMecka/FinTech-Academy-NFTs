"""
NFT: FinTech Edition!
"""
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Signer, Asset
import requests
from dotenv import load_dotenv
import os
import sys
# Load Enviornment Variables
load_dotenv()

# 1. Load Keys
# In this case this account will be the distributor.
server = Server("https://horizon-testnet.stellar.org")

secret_key = os.getenv("NFT_WALLET_HOLDER")
if secret_key is None:
    print("You haven't supplied an Enviornment variable with a Secret Key called NFT_WALLET_HOLDER!")
    sys.exit(1)

owner_key = Keypair.from_secret(secret_key)

ASSET_NAME = os.getenv("NFT_ASSET_NAME")
if ASSET_NAME is None:
    print("You haven't supplied an Enviornment variable with a NFT Asset's name called NFT_ASSET_NAME")
    sys.exit(1)


STELLAR_TOML_LOCATION = os.getenv("STELLAR_TOML_LOCATION")    
if STELLAR_TOML_LOCATION is None:
    print("You haven't supplied an Enviornment variable with the location for a stellar toml file name called STELLAR_TOML_LOCATION")
    sys.exit(1)

# 2. Create Another account
# In this case this one will Issue the new token
random_keypair = Keypair.random()
random_keypair_pub_key = random_keypair.public_key
random_keypair_priv_key = random_keypair.secret

# 3. Fund Issuer account using TestBot
print("Funding Random Account...")

url = 'https://friendbot.stellar.org'
response = requests.get(url, params={'addr': random_keypair.public_key})
print(f"Friendbot responded with {response}")

print(f"ISSUER: {random_keypair_pub_key}")
IPFS_HASH = input("BEFORE PROCEEDING. You will need to use the following public key in your metadata.json as an ISSUER. Provide an IPFS hash here!")
if IPFS_HASH == '' or IPFS_HASH is None:
    print("You haven't supplied an IPFS_HASH")
    sys.exit(1)

# 4. Create an object to represent the new asset
asset = Asset(ASSET_NAME, random_keypair_pub_key)

# 5. Distributor Account should trust the Issuing account
print("Building Transaction...")

base_fee = server.fetch_base_fee()
stellar_account = server.load_account(owner_key.public_key)

transaction = (
    TransactionBuilder(
        source_account=stellar_account,
        network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
        base_fee=base_fee,
    )
    .append_change_trust_op(
        asset=asset
    )
    .build()
)

print('Signing Transaction...')
transaction.sign(secret_key)
response = server.submit_transaction(transaction)

print(f"This is the response from trusting the Issuer: {response}")

# 6. Now transfer some funds to the distributor account

print('Transfering Tokens from Issuer to Distributor...')
issuer_account = server.load_account(random_keypair_pub_key)
print(random_keypair_pub_key)

transaction = (
    TransactionBuilder(
        source_account=issuer_account,
        network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
        base_fee=base_fee,
    )
    .append_payment_op(
        destination=owner_key.public_key,
        amount="0.0000001", # Stroop, lowest amount 
        asset=asset
    ).append_manage_data_op(
        data_name = "ipfshash",
        data_value = IPFS_HASH
    ).append_set_options_op(
        home_domain = STELLAR_TOML_LOCATION,
        low_threshold=2,
        med_threshold=2,
        high_threshold=2
    )
    .build()
)

print('Signing Transaction...')
transaction.sign(random_keypair_priv_key)
response = server.submit_transaction(transaction)

print(f"Final response: {response}")
