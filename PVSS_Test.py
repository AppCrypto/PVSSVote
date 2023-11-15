from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
from solcx import compile_standard,install_solc
install_solc("0.8.0")
import time
import json  #to save the output in a JSON file
import time
import pvss  #Cryptographic primitive library 



global pk,sk,n,t
n=10    #tally_people /Registered Tallier
t=5     #The voting system need tallier to recover secret


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



key=pvss.keygen()
pk=key["pk"]  #Public key array
sk=key["sk"]  #Private key array
pk1=[0]
pk2=[0]
pk1.extend(int(pk[i][0]) for i in range(1,n+1))
pk2.extend(int(pk[i][1]) for i in range(1,n+1)) 
#PVSS Key Generation
#pvss setup



#First Test 
#vote Share Size
def Test1():
    Share=pvss.PvssVote(pvss.random_scalar(),1)
    print(Share)
    print(".............................v(size)................................")
    print(Share['v'])
    print(".............................c(size)................................")
    print(Share['c'])
    print(".............................U(size)................................")
    print(Share['U'])

#Second Test 
#Gas cost of both bilinear pairing
def Test2():
    Share1=pvss.PvssVote(pvss.random_scalar(),2)
    test1=pvss.dateconvert(Share1)    #Data conversion for bilinear pairing on-chain
    #Test different talliers, gas cost of voter_verify
    gas_estimate1=Contract.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).estimateGas()
    print("Voter_verify gas cost :   " ,gas_estimate1)
    #Test different talliers, gas cost of tallier_verify
    gas_estimate2=Contract.functions.Node_verify_link(test1["v1"],test1["v2"],test1["s1"],test1["s2"]).estimateGas()
    print("Tallier_verify gas cost :   " ,gas_estimate2)


#Third Test 
#The time cost of Share accumulation
def Test3():
    share=pvss.PvssVote(pvss.random_scalar(),2)
    share1=pvss.PvssVote(pvss.random_scalar(),2)

    starttime=time.time() #time test
    for i in range(500):  #accumulate time
        for j in range(1,n+1):   #Share accumulation for (v,c,u) of each vote, Shares are accumulate to share1,which is the first vote share
            share1["c"][j]=pvss.add(share1["c"][j],share["c"][j]) #accumulate c
            share1["v"][j]=pvss.add(share1["v"][j],share["v"][j]) #accumulate v
        share1["U"]=pvss.add(share1["U"],share["U"]) #accumulate U
    print("Accumulate 500times  cost: ",time.time()- starttime)  #time test

#Fourth Test 
#The gas cost of TallyResult
def Test4(): 
    acc=pvss.PvssVote(pvss.random_scalar(),2)
    dataacc=pvss.dateconvert(acc)   
    gas_estimate=votescore = Contract.functions.VoteTally(dataacc["s1"],dataacc["s2"], pvss.recover_secret4(acc["raw"]),int(acc["U"][0]),int(acc["U"][1])).estimateGas()
    print("VoteTally gas cost :   " ,gas_estimate)


#Fifth Test
#The time cost of voter cast his vote 
def Test5():
    starttime=time.time()
    acc=pvss.PvssVote(pvss.random_scalar(),2)
    t1=time.time()- starttime
    print("PVSS.Share() time cost: ",t1) 
    test1=pvss.dateconvert(acc)    
    starttime2=time.time()
    Contract.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).call({"from":w3.eth.accounts[0]})
    t2=time.time()- starttime
    print("PVSS.Verify() time cost: ",t2) 
    print("The voter finish vote all time cost: ",(t1+t2)) 


#system test
print("Test begin..................................................................")
Test1()
Test2()
Test3()
Test4()
Test5()
print("Test finish.................................................................")
