pragma solidity ^0.8.0;
pragma experimental ABIEncoderV2;
// import "../contracts/BN256G2.sol";
// import { StringUtils } from "	../contracts/stringUtil.sol";


// https://www.iacr.org/cryptodb/archive/2002/ASIACRYPT/50/50.pdf
contract IncentiveVote
{
	// p = p(u) = 36u^4 + 36u^3 + 24u^2 + 6u + 1
    uint256 constant FIELD_ORDER = 0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47;
	uint256 modp = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
    // Number of elements in the field (often called `q`)
    // n = n(u) = 36u^4 + 36u^3 + 18u^2 + 6u + 1
    uint256 constant GEN_ORDER = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001;

    uint256 constant CURVE_B = 3;

    // a = (p+1) / 4
    uint256 constant CURVE_A = 0xc19139cb84c680a6e14116da060561765e05aa45a1c72a34f082305b61f3f52;

	struct G1Point {
		uint X;
		uint Y;
	}

	// Encoding of field elements is: X[0] * z + X[1]
	struct G2Point {
		uint[2] X;
		uint[2] Y;
	}

	// (P+1) / 4
	function A() pure internal returns (uint256) {
		return CURVE_A;
	}

	function P() pure internal returns (uint256) {
		return FIELD_ORDER;
	}

	function N() pure internal returns (uint256) {
		return GEN_ORDER;
	}

	/// return the generator of G1
	function P1() pure internal returns (G1Point memory) {
		return G1Point(1, 2);
	}

	function HashToPoint(uint256 s)
        internal view returns (G1Point memory)
    {
        uint256 beta = 0;
        uint256 y = 0;

        // XXX: Gen Order (n) or Field Order (p) ?
        uint256 x = s % GEN_ORDER;

        while( true ) {
            (beta, y) = FindYforX(x);

            // y^2 == beta
            if( beta == mulmod(y, y, FIELD_ORDER) ) {
                return G1Point(x, y);
            }

            x = addmod(x, 1, FIELD_ORDER);
        }
    }


    /**
    * Given X, find Y
    *
    *   where y = sqrt(x^3 + b)
    *
    * Returns: (x^3 + b), y
    */
    function FindYforX(uint256 x)
        internal view returns (uint256, uint256)
    {
        // beta = (x^3 + b) % p
        uint256 beta = addmod(mulmod(mulmod(x, x, FIELD_ORDER), x, FIELD_ORDER), CURVE_B, FIELD_ORDER);

        // y^2 = x^3 + b
        // this acts like: y = sqrt(beta)
        uint256 y = expMod(beta, CURVE_A, FIELD_ORDER);

        return (beta, y);
    }


    // a - b = c;
    function submod(uint a, uint b) internal pure returns (uint){
        uint a_nn;

        if(a>b) {
            a_nn = a;
        } else {
            a_nn = a+GEN_ORDER;
        }

        return addmod(a_nn - b, 0, GEN_ORDER);
    }


    function expMod(uint256 _base, uint256 _exponent, uint256 _modulus)
        internal view returns (uint256 retval)
    {
        bool success;
        uint256[1] memory output;
        uint[6] memory input;
        input[0] = 0x20;        // baseLen = new(big.Int).SetBytes(getData(input, 0, 32))
        input[1] = 0x20;        // expLen  = new(big.Int).SetBytes(getData(input, 32, 32))
        input[2] = 0x20;        // modLen  = new(big.Int).SetBytes(getData(input, 64, 32))
        input[3] = _base;
        input[4] = _exponent;
        input[5] = _modulus;
        assembly {
            success := staticcall(sub(gas(), 2000), 5, input, 0xc0, output, 0x20)
            // Use "invalid" to make gas estimation work
            //switch success case 0 { invalid }
        }
        require(success);
        return output[0];
    }


	/// return the generator of G2
	function P2() pure internal returns (G2Point memory) {
		return G2Point(
			[11559732032986387107991004021392285783925812861821192530917403151452391805634,
			 10857046999023057135944570762232829481370756359578518086990519993285655852781],
			[4082367875863433681332203403145435568316851327593401208105741076214120093531,
			 8495653923123431417604973247489272438418190587263600148770280649306958101930]
		);
	}

	/// return the negation of p, i.e. p.add(p.negate()) should be zero.
	function g1neg(G1Point memory p) pure internal returns (G1Point memory) {
		// The prime q in the base field F_q for G1
		uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
		if (p.X == 0 && p.Y == 0)
			return G1Point(0, 0);
		return G1Point(p.X, q - (p.Y % q));
	}

	/// return the sum of two points of G1
	function g1add(G1Point memory p1, G1Point memory p2) view internal returns (G1Point memory r) {
		uint[4] memory input;
		input[0] = p1.X;
		input[1] = p1.Y;
		input[2] = p2.X;
		input[3] = p2.Y;
		bool success;
		assembly {
			success := staticcall(sub(gas(), 2000), 6, input, 0xc0, r, 0x60)
			// Use "invalid" to make gas estimation work
			//switch success case 0 { invalid }
		}
		require(success);
	}

	/// return the product of a point on G1 and a scalar, i.e.
	/// p == p.mul(1) and p.add(p) == p.mul(2) for all points p.
	function g1mul(G1Point memory p, uint s) view internal returns (G1Point memory r) {
		uint[3] memory input;
		input[0] = p.X;
		input[1] = p.Y;
		input[2] = s;
		bool success;
		assembly {
			success := staticcall(sub(gas(), 2000), 7, input, 0x80, r, 0x60)
			// Use "invalid" to make gas estimation work
			//switch success case 0 { invalid }
		}
		require (success);
	}

	/// return the result of computing the pairing check
	/// e(p1[0], p2[0]) *  .... * e(p1[n], p2[n]) == 1
	/// For example pairing([P1(), P1().negate()], [P2(), P2()]) should
	/// return true.
	function pairing(G1Point[] memory p1, G2Point[] memory p2) view internal returns (bool) {
		require(p1.length == p2.length);
		uint elements = p1.length;
		uint inputSize = elements * 6;
		uint[] memory input = new uint[](inputSize);
		for (uint i = 0; i < elements; i++)
		{
			input[i * 6 + 0] = p1[i].X;
			input[i * 6 + 1] = p1[i].Y;
			input[i * 6 + 2] = p2[i].X[0];
			input[i * 6 + 3] = p2[i].X[1];
			input[i * 6 + 4] = p2[i].Y[0];
			input[i * 6 + 5] = p2[i].Y[1];
		}
		uint[1] memory out;
		bool success;
		assembly {
			success := staticcall(sub(gas()	, 2000), 8, add(input, 0x20), mul(inputSize, 0x20), out, 0x20)
			// Use "invalid" to make gas estimation work
			//switch success case 0 { invalid }
		}
		require(success);
		return out[0] != 0;
	}

	/// Convenience method for a pairing check for two pairs.
	function pairingProd2(G1Point memory a1, G2Point memory a2, G1Point memory b1, G2Point memory b2) view internal returns (bool) {
		G1Point[] memory p1 = new G1Point[](2);
		G2Point[] memory p2 = new G2Point[](2);
		p1[0] = a1;
		p1[1] = b1;
		p2[0] = a2;
		p2[1] = b2;
		return pairing(p1, p2);
	}

	/// Convenience method for a pairing check for three pairs.
	function pairingProd3(
			G1Point memory a1, G2Point memory a2,
			G1Point memory b1, G2Point memory b2,
			G1Point memory c1, G2Point memory c2
	) view internal returns (bool) {
		G1Point[] memory p1 = new G1Point[](3);
		G2Point[] memory p2 = new G2Point[](3);
		p1[0] = a1;
		p1[1] = b1;
		p1[2] = c1;
		p2[0] = a2;
		p2[1] = b2;
		p2[2] = c2;
		return pairing(p1, p2);
	}

	/// Convenience method for a pairing check for four pairs.
	function pairingProd4(
			G1Point memory a1, G2Point memory a2,
			G1Point memory b1, G2Point memory b2,
			G1Point memory c1, G2Point memory c2,
			G1Point memory d1, G2Point memory d2
	) view internal returns (bool) {
		G1Point[] memory p1 = new G1Point[](4);
		G2Point[] memory p2 = new G2Point[](4);
		p1[0] = a1;
		p1[1] = b1;
		p1[2] = c1;
		p1[3] = d1;
		p2[0] = a2;
		p2[1] = b2;
		p2[2] = c2;
		p2[3] = d2;
		return pairing(p1, p2);
	}

    // Costs ~85000 gas, 2x ecmul, + mulmod, addmod, hash etc. overheads
	function CreateProof( uint256 secret, uint256 message )
	    public payable
	    returns (uint256[2] memory out_pubkey, uint256 out_s, uint256 out_e)
	{
		G1Point memory xG = g1mul(P1(), secret % N());
		out_pubkey[0] = xG.X;
		out_pubkey[1] = xG.Y;
		uint256 k = uint256(keccak256(abi.encodePacked(message, secret))) % N();
		G1Point memory kG = g1mul(P1(), k);
		out_e = uint256(keccak256(abi.encodePacked(out_pubkey[0], out_pubkey[1], kG.X, kG.Y, message)));
		out_s = submod(k, mulmod(secret, out_e, N()));
	}

	// Costs ~85000 gas, 2x ecmul, 1x ecadd, + small overheads
	function CalcProof( uint256[2] memory pubkey, uint256 message, uint256 s, uint256 e )
	    public payable
	    returns (uint256)
	{
	    G1Point memory sG = g1mul(P1(), s % N());
	    G1Point memory xG = G1Point(pubkey[0], pubkey[1]);
	    G1Point memory kG = g1add(sG, g1mul(xG, e));
	    return uint256(keccak256(abi.encodePacked(pubkey[0], pubkey[1], kG.X, kG.Y, message)));
	}
	

	//Bilinear pairing verification for distribute shares array (PVSS.Verify) ,  e(pki,vi)=e(ci, g1) , The array include all distribute shares
	function Dealer_verify_link(  
		uint256[2][] memory v1, uint256[2][]  memory v2, 
		uint256[] memory  c1 , uint256[] memory c2 , 
		uint256[] memory pk1, uint256[] memory pk2
		) 
	public payable 
	returns (bool)
    {   
		uint elements=pk1.length;
		
		for(uint i=1;i<=elements-1;i++) //11=error
		{
			if (!Dealer_verify(v1[i],v2[i],c1[i],c2[i],pk1[i],pk2[i])) //single bilinear pairing for (i)th distribute share
			{
				return false;
			}		
		}       
		return true;
    }      
		
	//Bilinear pairing verification for distribute shares (PVSS.Verify) ,  e(pki,vi)=e(ci, g1)
	function Dealer_verify(
		uint256[2] memory v1, uint256[2]  memory v2, 
		uint256  c1 , uint256  c2, 
		uint256  pk1,uint256  pk2)  
	public payable 
	returns (bool)
    {   
        G1Point[] memory g1points = new G1Point[](2);
		G2Point[] memory g2points = new G2Point[](2);
        uint p = 21888242871839275222246405745257275088696311157297823662689037894645226208583;	
		g1points[0].Y=pk2;
		g1points[0].X=pk1;
	
		g1points[1].X = c1;
		g1points[1].Y = c2;
		g2points[0].X = v1;
		g2points[0].Y = v2;
		g2points[1] = P2();
		g1points[1].Y = p - g1points[1].Y;
		if (!pairing(g1points, g2points))
		{
			return false;
		}
		return true;		
    }

	//Bilinear pairing verification for decrypted share   ,e(g2,si)=e(vi,g1)
	function Node_verify(
		uint256[2] memory v1,uint256[2] memory v2,
		uint s1,uint s2
	)
	public payable 
	returns (bool)
	{
		G1Point[] memory g1points = new G1Point[](2);
		G2Point[] memory g2points = new G2Point[](2);
        uint256 p = 21888242871839275222246405745257275088696311157297823662689037894645226208583;	
		g1points[0].X=s1;
		g1points[0].Y=s2;
		g1points[1] = P1();
		g2points[0] = P2();
		g2points[1].X = v1;
		g2points[1].Y = v2;
		g1points[1].Y = p - g1points[1].Y;
		if (!pairing(g1points, g2points))
		{
			return false;
		}
		return true;	
	}
	//Bilinear pairing verification for decrypted share array  ,e(g2,si)=e(vi,g1),  The array include all decrypted shares
	function Node_verify_link(
		uint256[2][] memory v1, uint256[2][]  memory v2,
		uint256[] memory s1,uint256[] memory s2
	)
	public payable
	returns (bool)
	{
		uint elements=s1.length;//to get the array length 
		for(uint i=1;i<=elements-1;i++)
		{
			if(!Node_verify(v1[i],v2[i],s1[i],s2[i])) //single bilinear pairing for (i)th decrypted share
			{
				return false;
			}
		}
		return true;
	}

	//PVSS.Reconstruction (on-chain) 
	function Secret_recover( 
		uint256  share,  //g^si
		uint256  lagrange_coefficient)  
	public payable 
	returns (G1Point memory r)
	{
		//uint256 s = share;
		G1Point memory xG = g1mul(P1(), share % N());
		G1Point memory yG = g1mul(xG,lagrange_coefficient);

		return  yG;  //recover g^s
	}

	//PVSS.Reconstruction (on-chain) and compute vote result  (ver.1)
	function VoteAccumula(  
		uint256[] memory share, 
		uint256[] memory lagrange_coefficient
	)
	public payable
	returns (G1Point memory r)
	{
		G1Point memory acc = P1();// acc=g1
		uint elements = share.length;
		for(uint i=1;i <= elements-1;i++)
		{
			
			acc = g1add(acc,Secret_recover(share[i],lagrange_coefficient[i])); //compute g^(s1+s2+...s_k),k is number of vote 
		}
		
		return g1add(acc,g1neg(P1()));//return g^((s1+s2+...s_k+1)-1),   k is number of vote 
	}

	//PVSS.Reconstruction (on-chain) and compute vote result  (ver.2)
	//c1,c2 is x,y of decrypted cumulative shares array
	//lagrange_coefficient is lagrange_coefficient array for recover 
	function VoteTally(
		uint256[] memory  c1 , uint256[] memory c2 , uint256[] memory lagrange_coefficient,uint u1,uint u2
	)
	public payable
	returns (G1Point memory )
	{	
		G1Point memory g1u;
		g1u.X=u1; //u1 is x of cumulative U 
		g1u.Y=u2; //u1 is y of cumulative U 
		G1Point memory g1points;
		G1Point memory acc=P1(); //acc=g
		uint elements = lagrange_coefficient.length;  //get array length
		for(uint i=1;i<=elements-1;i++)
		{
			g1points.X = c1[i];
			g1points.Y = c2[i];
			
			acc=g1add(acc,g1mul(g1points,lagrange_coefficient[i])); //compute g^(s1+s2+...s_length),length is number of vote 
		}
		acc=g1add(acc,g1neg(P1()));//the above acc is g^(s1+s2+...s_length)*g, so we need to g^(s1+s2+...s_length)*g/g to compute g^(s1,s2,...)
		acc=g1add(g1u,g1neg(acc)); //lastly, we compute vote by g^(s1+s2+...+v1+v2+...)/g^(s1+s2+...) get g^(v1+v2+...)
		return acc;    //return the vote result :g^(v1+v2+...)
	}

    struct Votetask{
        string vote;
        uint  tasktime;
        uint256 Vote_fee; 
        address Task_publisher;   
        uint256 n;       //The number of vote required to complete the task
        address[] vote_people;//成功投票的人
        address[] tally_people;//成功唱票的人
        address[] deposit_people;//质押资金的账号
    }

    mapping (address => Votetask) public Votetasks; // The initiator address is mapped to the voting task
	//The initiator begin a votetask invoke new_vote function
    function new_vote(string memory vote,address Task_publisher,uint256 Vote_fee, uint256 n) public payable
    {
        require(msg.value==Vote_fee);
        Votetasks[Task_publisher].vote = vote;
        Votetasks[Task_publisher].Task_publisher = Task_publisher;
        Votetasks[Task_publisher].Vote_fee = Vote_fee;
        Votetasks[Task_publisher].n = n;
        Votetasks[Task_publisher].tasktime = block.timestamp;
    }
    function deposit(address Task_publisher) public payable 
    {
		//If tallier deposit Success,then we put the tallier address into deposit_people
        require(msg.value==(Votetasks[Task_publisher].Vote_fee)/10);
        Votetasks[Task_publisher].deposit_people.push(msg.sender);
    }

    function votesuccess(address Task_publisher) public{
        Votetasks[Task_publisher].vote_people.push(msg.sender);
		//If the vote is successful, the voter address is put in vote_people
    }

    function record(address Task_publisher, int8 verify) external
    {
        require(block.timestamp <= Votetasks[Task_publisher].tasktime + 10 minutes, "Vote time exceeded");
		//It is necessary to complete the accumulation of shares and upload them within the specified time
         if (verify ==  1) {
			//When the share accumulation is complete, the player is added to the array tally_people
            Votetasks[Task_publisher].tally_people.push(msg.sender);
        }
    }


    function success_distribute(address Task_publisher) public {
		//When the result of the vote comes out, the task is completed
		//We will reward each address in the vote_people array with an equal share of the Digital assets
        for (uint i = 0; i < Votetasks[Task_publisher].vote_people.length; i++)
        {
            address payable recipient = payable( Votetasks[Task_publisher].vote_people[i]);
            uint amount=(Votetasks[Task_publisher].Vote_fee/5)/(Votetasks[Task_publisher].vote_people.length);
            recipient.transfer(amount);
        }
        //We will reward each address in the tally_people array with an equal share of the Digital assets
		//We also will return  deposited Digital assets of tally_poeple
        for (uint i = 0; i < Votetasks[Task_publisher].tally_people.length; i++)
        {
            address payable recipient2 = payable(Votetasks[Task_publisher].tally_people[i]);
            uint amount=(((Votetasks[Task_publisher].Vote_fee/5)*4/(Votetasks[Task_publisher].tally_people.length))+(Votetasks[Task_publisher].Vote_fee/10));
            recipient2.transfer(amount);
        }
		
    }



    function bytesToUint(bytes32 b) public pure returns (uint256) {
    	uint256 number;
    	for (uint256 i = 0; i < b.length; i++) {
        	number = number + uint8(b[i]) * (2**(8 * (b.length - (i + 1))));
    	}
    	return number;
	}

	function randomness() public view returns (uint256)		
	{
		uint timestamp = block.timestamp;
    	bytes32 hash = keccak256(abi.encodePacked(timestamp));
        uint256 random= (bytesToUint(hash)% (modp));
    	return random ;
	}


	function cverify(uint256 c, uint256 d0, uint256 d1) public view returns (bool)
	{
		if(c!=((d0+d1)%(modp)))
		{
			return false;
		}
		return true;
	}

	function bVerify(uint256 b0x , uint256 b0y , uint256 b00x , uint256 b00y) public view returns (bool)
	{
		assert(b0x == b00x);
		assert(b0y == b00y);
		//assert(a1[0] == a11[0]);
		//assert(a1[1] == a11[1]);

		return true;
	}
	function aVerify(uint256 a0x1 , uint256 a0x2 , uint256 a0y1 , uint256 a0y2 , uint256 a00x1, uint256 a00x2, uint256 a00y1 , uint256 a00y2) public view returns (bool)
	{
		assert(a0x1 == a00x1);
		assert(a0x2 == a00x2);
		assert(a0y1 == a00y1);
		assert(a0y2 == a00y2);
		return true;
	}

	//function failed_distribute()

    function show(address Task_publisher) public view
        returns (address[] memory ,address[] memory ,address[] memory)
    {
		//Look at the array of all the addresses of the task at this point
        return ( Votetasks[Task_publisher].vote_people,  Votetasks[Task_publisher].tally_people, Votetasks[Task_publisher].deposit_people);
    }

	
}	
