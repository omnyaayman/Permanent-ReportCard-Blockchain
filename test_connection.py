from web3 import Web3

GANACHE_URL = "http://127.0.0.1:7545"

web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if web3.is_connected():
    print("Connected to Ganache successfully")
    print("Latest block:", web3.eth.block_number)
    print("First account:", web3.eth.accounts[0])

    balance = web3.eth.get_balance(web3.eth.accounts[0])
    print("First account balance:", web3.from_wei(balance, "ether"), "ETH")
else:
    print("Failed to connect to Ganache")