from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
from solcx import compile_standard,install_solc
install_solc("0.8.0")
import time
import json  #to save the output in a JSON file
import time
import pvssfortest  #Cryptographic primitive library 
import sys  


global pk,sk,nn,tt
nn=10    #tally_people /Registered Tallier
tt=5     #The voting system need tallier to recover secret


with open("contracts/IncentiveVote.sol", "r") as file:
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



key=pvssfortest.keygen(100)
pk=key["pk"]  #Public key array
sk=key["sk"]  #Private key array
pk1=[0]
pk2=[0]
pk1.extend(int(pk[i][0]) for i in range(1,101))
pk2.extend(int(pk[i][1]) for i in range(1,101)) 
#PVSS Key Generation
#pvss setup



def verifygastest(n):
    key=pvssfortest.keygen(n)
    pk=key["pk"]  #Public key array
    sk=key["sk"]  #Private key array
    pk11=[0]
    pk22=[0]
    pk11.extend(int(pk[i][0]) for i in range(1,n+1))
    pk22.extend(int(pk[i][1]) for i in range(1,n+1)) 
    #PVSS Key Generation
    Share1=pvssfortest.PvssVote(pvssfortest.random_scalar(),2,n,int(n/2))
    test1=pvssfortest.dateconvert(Share1,n)    #Data conversion for bilinear pairing on-chain
    #Test different talliers, gas cost of voter_verify
    #Contract.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk11,pk22).call({"from":w3.eth.accounts[0]})
    gas_estimate1=Contract.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk11,pk22).estimateGas()
    gas_estimate2=Contract.functions.Node_verify_link(test1["v1"],test1["v2"],test1["s1"],test1["s2"]).estimateGas()
    print("{",n,",",int(n/2),"}"," Voter_verify gas cost :  " ,gas_estimate1,"   Tallier_verify gas cost :  ",gas_estimate2)
    #Test different talliers, gas cost of tallier_verify

def Accumulatetest(times,n):

    share=pvssfortest.PvssVote(pvssfortest.random_scalar(),2,n,int(n/2))
    share1=pvssfortest.PvssVote(pvssfortest.random_scalar(),2,n,int(n/2))
    starttime=time.time() #time test
    for i in range(times):  #accumulate time
        for j in range(1,n+1):   #Share accumulation for (v,c,u) of each vote, Shares are accumulate to share1,which is the first vote share
            share1["c"][j]=pvssfortest.add(share1["c"][j],share["c"][j]) #accumulate c
            share1["v"][j]=pvssfortest.add(share1["v"][j],share["v"][j]) #accumulate v
        share1["U"]=pvssfortest.add(share1["U"],share["U"]) #accumulate U
    print("Accumulate ",times,"times  cost: ",time.time()- starttime)  #time test


def ReconGasTest(n):

    acc=pvssfortest.PvssVote(pvssfortest.random_scalar(),2,n,int(n/2))
    dataacc=pvssfortest.dateconvert(acc,n)   
    gas_estimate=votescore = Contract.functions.VoteTally(dataacc["s1"],dataacc["s2"], pvssfortest.recover_secret4(acc["raw"]),int(acc["U"][0]),int(acc["U"][1])).estimateGas()
    print(n," VoteTally gas cost :   " ,gas_estimate)


def VoterTimeTest(n):
    key=pvssfortest.keygen(n)
    pk=key["pk"]  #Public key array
    sk=key["sk"]  #Private key array
    pk11=[0]
    pk22=[0]
    pk11.extend(int(pk[i][0]) for i in range(1,n+1))
    pk22.extend(int(pk[i][1]) for i in range(1,n+1)) 
    starttime=time.time()
    acc=pvssfortest.PvssVote(pvssfortest.random_scalar(),2,n,int(n/2))
    t1=time.time()- starttime

    test1=pvssfortest.dateconvert(acc,n)    
    starttime2=time.time()
    Contract.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk11,pk22).call({"from":w3.eth.accounts[0]})
    t2=time.time()- starttime
    print("In",n,"Tallier ","Every Voter PVSS.Share() time cost: ",t1," PVSS.Verify() time cost: ",t2," The voter finish vote all time cost: ",(t1+t2)) 

#First Test 
#vote Share Size
def Test1():
    print("..............................................Test1 begin..................................................................")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,2,1)
    print("The size of the {2,1}  V: "+str(len(str(Share['v'])))+"  bytes, C: "+str(len(str(Share['c'])))+"  bytes, U: "+str(len(str(Share['U'])))+" bytes")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,4,2)
    print("The size of the {4,2}  V: "+str(len(str(Share['v'])))+" bytes, C: "+str(len(str(Share['c'])))+"  bytes, U: "+str(len(str(Share['U'])))+" bytes")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,6,3)
    print("The size of the {6,3}  V: "+str(len(str(Share['v'])))+" bytes, C: "+str(len(str(Share['c'])))+"  bytes, U: "+str(len(str(Share['U'])))+" bytes")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,8,4)
    print("The size of the {8,4}  V: "+str(len(str(Share['v'])))+" bytes, C: "+str(len(str(Share['c'])))+" bytes, U: "+str(len(str(Share['U'])))+" bytes")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,10,5)
    print("The size of the {10,5} V: "+str(len(str(Share['v'])))+" bytes, C: "+str(len(str(Share['c'])))+" bytes, U: "+str(len(str(Share['U'])))+" bytes")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,12,6)
    print("The size of the {12,6} V: "+str(len(str(Share['v'])))+" bytes, C: "+str(len(str(Share['c'])))+" bytes, U: "+str(len(str(Share['U'])))+" bytes")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,14,7)
    print("The size of the {14,7} V: "+str(len(str(Share['v'])))+" bytes, C: "+str(len(str(Share['c'])))+" bytes, U: "+str(len(str(Share['U'])))+" bytes")
    Share=pvssfortest.PvssVote(pvssfortest.random_scalar(),1,16,8)
    print("The size of the {16,8} V: "+str(len(str(Share['v'])))+" bytes, C: "+str(len(str(Share['c'])))+" bytes, U: "+str(len(str(Share['U'])))+" bytes")
    print("..............................................Test1 end..................................................................")
    #vote size of different tallier
    
#Second Test 
#Gas cost of both bilinear pairing
def Test2():
    print("..............................................Test2 begin..................................................................")
    verifygastest(2)
    verifygastest(4)
    verifygastest(6)
    verifygastest(8)
    verifygastest(10)
    verifygastest(12)
    verifygastest(14)
    #verifygastest(16)
    print("..............................................Test2 end..................................................................")


#Third Test 
#The time cost of Share accumulation
def Test3():
    print("..............................................Test3 begin..................................................................")
    Accumulatetest(100,10) #(times,n) ,where times is accumulation times and n is number of tallier
    Accumulatetest(200,10)
    Accumulatetest(300,10)
    Accumulatetest(400,10)
    Accumulatetest(500,10)
    print("..............................................Test3 end..................................................................")

#Fourth Test 
#The gas cost of TallyResult
def Test4(): 
    print("..............................................Test4 begin..................................................................")
    ReconGasTest(2)  #n is number of tallier 
    ReconGasTest(4)
    ReconGasTest(6)
    ReconGasTest(8)
    ReconGasTest(10)
    ReconGasTest(12)
    ReconGasTest(14)
    ReconGasTest(16)
    print("..............................................Test4 end..................................................................")

#Fifth Test
#The time cost of voter cast his vote 
def Test5():
    print("..............................................Test5 begin..................................................................")
    VoterTimeTest(2)  #VoterTimeTest(n) for voter invoke function to cast his vote ,where n is number of tallier
    VoterTimeTest(4)
    VoterTimeTest(6)
    VoterTimeTest(8)
    VoterTimeTest(10)
    VoterTimeTest(12)
    VoterTimeTest(14)
    VoterTimeTest(16)
    print("..............................................Test5 end..................................................................")

#system test
print("..............................................All Test begin..................................................................")
Test1()
Test2()
Test3()
Test4()
Test5()
print("..............................................All Test finish.................................................................")
