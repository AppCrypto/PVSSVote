import random
import secrets
import sympy # consider removing this dependency, only needed for mod_inverse
import re
import numpy as np
import hashlib
import datetime
import sys
from py_ecc.bn128 import G1, G2
from py_ecc.bn128 import add, multiply, neg, pairing, is_on_curve
from py_ecc.bn128 import curve_order as CURVE_ORDER
from py_ecc.bn128 import field_modulus as FIELD_MODULUS
from typing import Tuple, Dict, List, Iterable, Union
global pk,sk,n,t
sk=[0]
pk=[0]
n=10    #tally_people
t=5

def random_scalar() -> int:
    """ Returns a random exponent for the BN128 curve, i.e. a random element from Zq.
    """
    return secrets.randbelow(CURVE_ORDER)

def keygen() :
    """ Generates a random keypair on the BN128 curve.
        The public key is an element of the group G1.
        This key is used for deriving the encryption keys used to secure the shares.
        This is NOT a BLS key pair used for signing messages.
    """
    global sk,pk
    sk.extend([random_scalar() for i in range(1,n+1)])
    pk.extend([multiply(G1, sk[i]) for i in range(1,n+1)]) #only need 1-10
    return {"pk":pk,"sk":sk}

def share_secret(secret:int ,sharenum:int ,threshold: int)-> Dict[int, int]:

    coefficients = [secret] + [random_scalar() for j in range(threshold-1)]
    #coefficients=[5]+[x for x in range(1,threshold)]
    
    #print(coefficients)
    def f(x: int) -> int:
        """ evaluation function for secret polynomial
        """
        return (
            sum(coef * pow(x, j, CURVE_ORDER) for j, coef in enumerate(coefficients)) % CURVE_ORDER
        )
    shares = { x:f(x) for x in range(1,sharenum+1) }
    #print(shares)
    return shares

def dateconvert(res):
    v1=[[0,0]]
    v2=[[0,0]]
    c1=[0]
    c2=[0]

    si=[0]
    s1=[0]
    s2=[0]
    for i in range(1,n+1):
    #print(dd["v"][i][0])
    
        number1 = re.findall("\d+",str(res["v"][i][0]))
        vv1=[]
        #print(number[0])
        #print(number[1])#str
        vv1.append(int(number1[1]))
        vv1.append(int(number1[0]))
        #print(vv1)
        v1.append(vv1)
    
    #v1.extend()
    #print(dd["v"][i][1])

    for i in range(1,n+1):
    #print(dd["v"][i][0])
    
        number2 = re.findall("\d+",str(res["v"][i][1]))
        vv2=[]
        #print(number[0])
        #print(number[1])#str
        vv2.append(int(number2[1]))
        vv2.append(int(number2[0]))
        #print(vv1)
        v2.append(vv2)
    for i in range(1,n+1):
        si.extend([multiply(res["c"][i],sympy.mod_inverse((sk[i]) % CURVE_ORDER, CURVE_ORDER))])

    c1.extend(int(res["c"][i][0]) for i in range(1,n+1))
    c2.extend(int(res["c"][i][1]) for i in range(1,n+1))
    s1.extend(int(si[i][0]) for i in range(1,1+n))
    s2.extend(int(si[i][1]) for i in range(1,1+n))
    return {"c1":c1,"c2":c2,"v1":v1,"v2":v2,"s1":s1,"s2":s2}


def PvssVote(secret:int,vote:int):
    PVSSshare=share_secret(secret,n,t)
    #print(PVSSshare[1])
    #print(PVSSshare[2])
    #print(type(PVSSshare[1]))
    #print("test11111")
    U=multiply(G1,(secret+vote))
    S=multiply(G1,(secret))
    v=[0]
    c=[0]
    v.extend([multiply(G2,PVSSshare[i]) for i in range(1,n+1)])
    c.extend([multiply(pk[i],PVSSshare[i]) for i in range(1,n+1)])
    #print(U)
    res={"v":v,"c":c,"U":U,"S":S,"raw":PVSSshare}
    return res 

def recover_secret3(num) -> int:   #计算拉格朗日系数的
    """ Recovers a shared secret from t VALID shares.
    """

    def lagrange_coefficient(i: int) -> int:
        result = 1
        for j in (1,num+1):
            if i != j:
                result *= j * sympy.mod_inverse((j - i) % CURVE_ORDER, CURVE_ORDER)
                result %= CURVE_ORDER
        return result
    #print(shares.items())
    lar=[0]
    lar.extend([lagrange_coefficient(i) for i in range(1,num+1)])

    return lar

def recover_secret4(shares: Dict[int, int]) -> int:
    """ Recovers a shared secret from t VALID shares.
    """

    def lagrange_coefficient(i: int) -> int:
        result = 1
        for j in shares:
            if i != j:
                result *= j * sympy.mod_inverse((j - i) % CURVE_ORDER, CURVE_ORDER)
                result %= CURVE_ORDER
        return result
    #print(shares.items())
    lar=[0]
    lar.extend([lagrange_coefficient(i) for i in range(1,len(shares)+1)])

    return lar



def Vote_all(votenum:int):
    
    share1=PvssVote(random_scalar(),0)
    test1=dateconvert(share1)
    ret = ctt.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).call({"from":w3.eth.accounts[0]})
    print(ret)
    #gas_estimate = ctt.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).estimateGas()
    #print("Dealer verify gas cost:",gas_estimate)

    print("NO."+str(1)+"VoteDone")
    for i in range(1,votenum):
        share=PvssVote(random_scalar(),1)
        test1=dateconvert(share)
        ret = ctt.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).call({"from":w3.eth.accounts[0]})
        print(ret)
        for j in range(1,n+1):
            share1["c"][j]=add(share1["c"][j],share["c"][j])
            share1["v"][j]=add(share1["v"][j],share["v"][j])

        share1["U"]=add(share1["U"],share["U"])
        #share1["S"]=add(share1["S"],share["S"])
        print("NO."+str(i+1)+"VoteDone")

    test1=dateconvert(share1)
    ret = ctt.functions.Node_verify_link(test1["v1"],test1["v2"],test1["s1"],test1["s2"]).call({"from":w3.eth.accounts[0]})
    print("Acc verify_done"+"   "+"The result is "+str(ret))
    votescore = ctt.functions.VoteTally(test1["s1"],test1["s2"], recover_secret3(share1["raw"]),int(share1["U"][0]),int(share1["U"][1])).call({"from":w3.eth.accounts[0]})
    #gas_estimate = ctt.functions.VoteTally(test1["s1"],test1["s2"], recover_secret3(share1["raw"]),int(share1["U"][0]),int(share1["U"][1])).estimateGas()
    #print("VoteTally gas cost:",gas_estimate)
    return votescore

def VoteDatabase(votenum):
    votedate=[0]
    votedate.extend([multiply(G1,i) for i in range(1,votenum+1)])
    #print(votedate)
    return votedate

def Tallying(num):
    Votealldate=VoteDatabase(num)
    #starttime=time.time() #time test
    result=Vote_all(num)
    for i in range(0,num+1):
        if (str(result)==str(Votealldate[i])):
            print("result"+str(i)+"votes")
    #print("PvssVote cost ",time.time()- starttime)  #time test

