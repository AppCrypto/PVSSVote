from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
from solcx import compile_standard,install_solc
install_solc("0.8.0")
import time
import json #to save the output in a JSON file
import time
import pvss



global pk,sk,n,t
n=10    #tally_people
t=5


with open("/home/ozr/IncentiveVote/contracts/IncentiveVote.sol", "r") as file:
    contact_list_file = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"IncentiveVote.sol": {"content": contact_list_file}},
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

#print(compiled_sol)
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)
# get bytecode
bytecode = compiled_sol["contracts"]["IncentiveVote.sol"]["IncentiveVote"]["evm"]["bytecode"]["object"]
# get abi
abi = json.loads(compiled_sol["contracts"]["IncentiveVote.sol"]["IncentiveVote"]["metadata"])["output"]["abi"]
# Create the contract in Python
contract = w3.eth.contract(abi=abi, bytecode=bytecode)



chain_id = 5777
accounts0 = w3.eth.accounts[0]
transaction_hash = contract.constructor().transact({'from': accounts0})
# 等待合约部署完成
transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
# 获取部署后的合约地址
contract_address = transaction_receipt['contractAddress']
print("合约已部署，地址：", contract_address)

Contract = w3.eth.contract(address=contract_address, abi=abi)

#key=pvss.keygen()


key=pvss.keygen()
pk=key["pk"]
sk=key["sk"]
pk1=[0]
pk2=[0]
pk1.extend(int(pk[i][0]) for i in range(1,n+1))
pk2.extend(int(pk[i][1]) for i in range(1,n+1)) 

#pvss setup
"""
accounts9 = w3.eth.accounts[9]
Contract.functions.new_vote("test",accounts0,30000000000000000000,3).transact({'from': accounts0,'value': 30000000000000000000})

for i in range(1,4):
    
    accounts = w3.eth.accounts[i]
    Contract.functions.deposit(accounts0).transact({'from': accounts, 'value': 3000000000000000000})
    Contract.functions.record(accounts0,1).transact({'from': accounts})

for i in range(6,9):

    accounts = w3.eth.accounts[i]
    Contract.functions.votesuccess(accounts0).transact({'from': accounts})


#print(Contract.functions.show(accounts0).transact({'from': accounts0}))

Contract.functions.success_distribute(accounts0).transact({'from': accounts0})
"""

def IncentiveVote():
    Contract.functions.new_vote("test",accounts0,30000000000000000000,3).transact({'from': w3.eth.accounts[0],'value': 30000000000000000000})
    #new vote distribute by accounts0 
    #pvss.setup
    #tally people choose  
    for i in range(1,4):
        Contract.functions.deposit(accounts0).transact({'from': w3.eth.accounts[i], 'value': 3000000000000000000}) #deposit_fee is 1/10 vote_fee
        #Contract.functions.record(accounts0,1).transact({'from': accounts})

    #vote begin       4~8 vote
    share1=pvss.PvssVote(pvss.random_scalar(),1)
    test1=pvss.dateconvert(share1)
    Contract.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).call({"from":w3.eth.accounts[4]})
    Contract.functions.votesuccess(accounts0).transact({'from': w3.eth.accounts[4]})
    print("NO."+str(4)+"  address : "+str(w3.eth.accounts[4])+"  VoteDone")
    for i in range(5,8):
        share=pvss.PvssVote(pvss.random_scalar(),2)
        test1=pvss.dateconvert(share1)
        Contract.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).call({"from":w3.eth.accounts[i]})
        Contract.functions.votesuccess(accounts0).transact({'from': w3.eth.accounts[i]})
        for j in range(1,n+1):
            share1["c"][j]=pvss.add(share1["c"][j],share["c"][j])
            share1["v"][j]=pvss.add(share1["v"][j],share["v"][j])
        share1["U"]=pvss.add(share1["U"],share["U"])
        print("NO."+str(i)+"  address : "+str(w3.eth.accounts[i])+"  VoteDone")
    

    all_votescore=[]
    dataacc=pvss.dateconvert(share1)
    for i in range(1,4):
        Contract.functions.Node_verify_link(dataacc["v1"],dataacc["v2"],dataacc["s1"],dataacc["s2"]).call({"from":w3.eth.accounts[i]})
        votescore = Contract.functions.VoteTally(dataacc["s1"],dataacc["s2"], pvss.recover_secret4(share1["raw"]),int(share1["U"][0]),int(share1["U"][1])).call({"from":w3.eth.accounts[i]})
        all_votescore.extend([votescore])
        Contract.functions.record(accounts0,1).transact({'from': w3.eth.accounts[i]})

    #tally_result check
    database=pvss.VoteDatabase(n)
    for i in range(0,n+1):
        if (str(all_votescore[0])==str(database[i])):
            print("result : "+str(i)+"  votes")
    Contract.functions.success_distribute(accounts0).transact({'from': accounts0})

print("vote begin.............................")
IncentiveVote()
print("vote done..............................")
