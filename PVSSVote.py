import random
import secrets
import sympy # consider removing this dependency, only needed for mod_inverse
import re
import numpy as np
import hashlib
import datetime
import sys



from typing import Tuple, Dict, List, Iterable, Union
#from py_ecc.optimized_bn128 import G1, G2
#from py_ecc.optimized_bn128 import add, multiply, neg, normalize, pairing, is_on_curve
#from py_ecc.optimized_bn128 import curve_order as CURVE_ORDER
#from py_ecc.optimized_bn128 import field_modulus as FIELD_MODULUS
#from charm.toolbox.secretutil import SecretUtil
from py_ecc.typing import FQ,FQ2
from py_ecc.bn128 import G1, G2
from py_ecc.bn128 import add, multiply, neg, pairing, is_on_curve
from py_ecc.bn128 import curve_order as CURVE_ORDER
from py_ecc.bn128 import field_modulus as FIELD_MODULUS
#from py_ecc.typing import Optimized_Point3D
import time,sys

#G2=((11559732032986387107991004021392285783925812861821192530917403151452391805634,10857046999023057135944570762232829481370756359578518086990519993285655852781), (4082367875863433681332203403145435568316851327593401208105741076214120093531,8495653923123431417604973247489272438418190587263600148770280649306958101930))

from solcx import compile_standard,install_solc
install_solc("0.8.0")
import time
import sys
import json #to save the output in a JSON file
with open("/home/ozr/ElectronicVoting2/constracts/Vote.sol", "r") as file:
    contact_list_file = file.read()
    #print(contact_list_file)


#print("1")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Vote.sol": {"content": contact_list_file}},
        "settings": {
            "outputSelection": {
                "*": {
                     "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"] # output needed to interact with and deploy contract 
                }
            }
        },
    },
    solc_version="0.8.0",
)
#print("2")
#print(compiled_sol)
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)    
#print("3")
# get bytecode
bytecode = compiled_sol["contracts"]["Vote.sol"]["Vote"]["evm"]["bytecode"]["object"]
# get abi
abi = json.loads(compiled_sol["contracts"]["Vote.sol"]["Vote"]["metadata"])["output"]["abi"]


from web3 import Web3 
#print("4")
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
chain_id = 1337
address = "0x1dD19324F570C86CCa91037b219d419153708561" #quickstart need to change by ozr
private_key = "0x88c6bf3a34f0e1c84ff49c6d6505c7fda01b7058734010b1d87409ffb0b76a56" # leaving the private key like this is very insecure if you are working on real world project
# Create the contract in Python
ContactList = w3.eth.contract(abi=abi, bytecode=bytecode)
# Get the number of latest transaction
nonce = w3.eth.getTransactionCount(address)

transaction = ContactList.constructor().buildTransaction(
    {"chainId": chain_id, "gasPrice": w3.eth.gas_price, "from": address, "nonce": nonce}
)
sign_transaction = w3.eth.account.sign_transaction(transaction, private_key=private_key)
print("Deploying Contract!")
# Send the transaction
transaction_hash = w3.eth.send_raw_transaction(sign_transaction.rawTransaction)
# Wait for the transaction to be mined, and get the transaction receipt
print("Waiting for transaction to finish...")
transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
print(f"Done! Contract deployed to {transaction_receipt.contractAddress}")


ctt = w3.eth.contract(address=transaction_receipt.contractAddress, abi=abi)





PointG1 = Tuple[FQ, FQ]
PointG2 = Tuple[FQ2, FQ2]


global pk,sk,n,t
sk=[0]
pk=[0]
n=18
t=9
global S,PVSSshare
