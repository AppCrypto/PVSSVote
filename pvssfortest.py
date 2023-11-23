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
global pk,sk,nn,tt
sk=[0]
pk=[0]  
nn=10   #PVSS Total distribution 
tt=5    #PVSS threshold value

def random_scalar() -> int: #Generate random numbers
    """ Returns a random exponent for the BN128 curve, i.e. a random element from Zq.
    """
    return secrets.randbelow(CURVE_ORDER)

def keygen(n) : #PVSS Key Generation
    """ Generates a random keypair on the BN128 curve.
        The public key is an element of the group G1.
        This key is used for deriving the encryption keys used to secure the shares.
        This is NOT a BLS key pair used for signing messages.
    """
    global sk,pk
    sk.extend([random_scalar() for i in range(1,n+1)])  
    pk.extend([multiply(G1, sk[i]) for i in range(1,n+1)]) #only need 1-n
    return {"pk":pk,"sk":sk}

def share_secret(secret:int ,sharenum:int ,threshold: int)-> Dict[int, int]: # PVSS.Share(s,n,t) n is sharenum value .t is threshold value

    coefficients = [secret] + [random_scalar() for j in range(threshold-1)]
    #The polynomial coefficients 
    def f(x: int) -> int:
        """ evaluation function for secret polynomial
        """
        return (
            sum(coef * pow(x, j, CURVE_ORDER) for j, coef in enumerate(coefficients)) % CURVE_ORDER
        )
    shares = { x:f(x) for x in range(1,sharenum+1) }
    #print(shares)
    return shares

def dateconvert(res,n):    #Data conversion functions for bilinear pairing on-chain
    v1=[[0,0]]           #The function splits the x and y values of a point into arrays v1 and v2
    v2=[[0,0]]
    c1=[0]
    c2=[0]

    si=[0]     
    s1=[0]
    s2=[0]
    for i in range(1,n+1):
    
        number1 = re.findall("\d+",str(res["v"][i][0]))
        vv1=[]
        vv1.append(int(number1[1]))
        vv1.append(int(number1[0]))
        v1.append(vv1)
    
    for i in range(1,n+1):
    
        number2 = re.findall("\d+",str(res["v"][i][1]))
        vv2=[]
        vv2.append(int(number2[1]))
        vv2.append(int(number2[0]))
        v2.append(vv2)
    for i in range(1,n+1):
        si.extend([multiply(res["c"][i],sympy.mod_inverse((sk[i]) % CURVE_ORDER, CURVE_ORDER))])

    c1.extend(int(res["c"][i][0]) for i in range(1,n+1))
    c2.extend(int(res["c"][i][1]) for i in range(1,n+1))
    s1.extend(int(si[i][0]) for i in range(1,1+n))
    s2.extend(int(si[i][1]) for i in range(1,1+n))
    return {"c1":c1,"c2":c2,"v1":v1,"v2":v2,"s1":s1,"s2":s2} #c1 is x of c, c2 is y of c. And v1,v2,s1,s2 so on...


def PvssVote(secret:int,vote:int,n:int,t:int):  # voter invoke to generating voting data (v,c,u)   vote is the vote value
    PVSSshare=share_secret(secret,n,t)  #voter PVSS.share=(v,c) 
    U=multiply(G1,(secret+vote))     #u=g1^(s+v)  
    #S=multiply(G1,(secret))    #S=g1^s   #,"S":S
    v=[0]
    c=[0]
    v.extend([multiply(G2,PVSSshare[i]) for i in range(1,n+1)])  #v_i=g2^s_i 
    c.extend([multiply(pk[i],PVSSshare[i]) for i in range(1,n+1)]) #c_i=pk_i^s_i
    res={"v":v,"c":c,"U":U,"raw":PVSSshare}
    return res 


def recover_secret4(shares: Dict[int, int]) -> int:#计算拉格朗日系数的
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




def Vote_all(votenum:int):  #The whole voting process without Incentive mechanism 
    
    share1=PvssVote(random_scalar(),0)   #The first voter cast his vote   his vote value is 0 ,is changeable
    test1=dateconvert(share1)           #Data conversion for bilinear pairing on-chain
    ret = ctt.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).call({"from":w3.eth.accounts[0]})
    #PVSS.Verify to the vote for n tallier 
    print("PVSS.Verify result:",ret)

    print("NO."+str(1)+"VoteDone") #The first voter vote done  
    for i in range(1,votenum): #The second to the votenum,like the 2 to the 10 begin to vote 
        share=PvssVote(random_scalar(),1)  # voter cast  vote , his vote value is 1, changeable 
        test1=dateconvert(share)   #data conversion 
        ret = ctt.functions.Dealer_verify_link(test1["v1"],test1["v2"],test1["c1"],test1["c2"],pk1,pk2).call({"from":w3.eth.accounts[0]})
        #PVSS.Verify to the vote for n tallier 
        print("PVSS.Verify result:",ret)
        for j in range(1,n+1):            #Share accumulation for (v,c,u) of each vote, Shares are accumulate to share1,which is the first vote share
            share1["c"][j]=add(share1["c"][j],share["c"][j])  #accumulate c
            share1["v"][j]=add(share1["v"][j],share["v"][j])  #accumulate v

        share1["U"]=add(share1["U"],share["U"]) #accumulate U
        print("NO."+str(i+1)+"VoteDone")

    test1=dateconvert(share1)  #data conversion.  This includes decryption of the shares.
    ret = ctt.functions.Node_verify_link(test1["v1"],test1["v2"],test1["s1"],test1["s2"]).call({"from":w3.eth.accounts[0]})
    #Verification for accumulated Share. In order to ensure the correctness of the voting result.
    print("Acc verify_done"+"   "+"The result is "+str(ret))
    votescore = ctt.functions.VoteTally(test1["s1"],test1["s2"], recover_secret3(share1["raw"]),int(share1["U"][0]),int(share1["U"][1])).call({"from":w3.eth.accounts[0]})
    #PVSS.Reconstruction  (on-chain) to recover the result (g^(v1+v2+...v_k)) k is the vote number 
    return votescore  #return vote result


def VoteDatabase(votenum):  #Pre-processing : Produce all voting results in advance
    votedate=[0]
    votedate.extend([multiply(G1,i) for i in range(1,votenum+1)])
    return votedate

def Tallying(num):     # Compare the result with the pre-processed result and find the same value g^v
    Votealldate=VoteDatabase(num)

    result=Vote_all(num)
    for i in range(0,num+1):
        if (str(result)==str(Votealldate[i])):
            print("result:  "+str(i)+"   votes")


