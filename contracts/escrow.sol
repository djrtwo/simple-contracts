pragma solidity ^0.4.11;

// v0.0.2
// Author(s): Danny Ryan

// Contract in Alpha. For educational purposes only

// # Escrow Contract #
// Involves three 'actors' -- 'sender', 'recipient', 'arbitrator'
// Holds Ether from 'sender' to be transferred to 'recipient'.
// Ether in contract is transferred to 'recipient' when two of the three 'actors' `confirm`.
// Contract can be `void`ed by 'sender' after `block.timestamp` is past 'timestampExpired'
// Ether is transferred to 'sender' upon successful `void`.

contract Escrow {
    /*
        Escrow is initialized with references to three parties (addresses)
        as well as the contract expireation timestamp
        The amount to be held in escrow can be sent upon initialization or in any transaction after.
        'timestampExpired' must be in the future.
    */
    function Escrow(address _sender, address _recipient, address _arbitrator, uint _timestampExpired) payable {
        assert(_timestampExpired > now);

        actors.push(_sender);
        actors.push(_recipient);
        actors.push(_arbitrator);
        timestampExpired = _timestampExpired;
    }

    /*
       Any of the initially specified actors can call confirm().
       Once there are enough confirmations (2) confirm releases funds to recipient.
    */
    function confirm() only_actor {
        confirmations[msg.sender] = true;
        if (isConfirmed()) {
            // use call to forward gas in case complex function receives gas
            assert(recipient().call.value(this.balance)());
        }
    }

    /*
        Sender can void escrow agreement after expiration.
        Voiding sends all funds held in contract back to the sender.
    */
    function void() only_sender {
        assert(now > timestampExpired);

        // use call to forward gas in case complex function receives gas
        assert(sender().call.value(this.balance)());
    }

    /*
       Sender of funds in contract.
       Only party that can void and return funds
    */
    function sender() constant returns (address) {
        return actors[0];
    }

    /*
       Recipient of funds in contract.
       Receives funds after two confirms from distinct valid parties
    */
    function recipient() constant returns (address) {
        return actors[1];
    }

    /*
       Arbitrator of escrow contract
       Can act as 1 of the 3 required actors for `confirm`ing
    */
    function arbitrator() constant returns (address) {
        return actors[2];
    }

    /*
       Count number of confirms
       returns true if two or more
    */
    function isConfirmed() constant returns (bool) {
        uint confCount = 0;
        for (uint i = 0; i < actors.length; i++) {
            if (confirmations[actors[i]]) {
                confCount++;
            }
        }
        return (confCount >= 2);
    }

    /*
       returns true if address is either the sender, recipient, or arbitrator
    */
    function isActor(address addr) constant returns (bool) {
        for (uint i = 0; i < actors.length; i++) {
            if (actors[i] == addr) return true;
        }
        return false;
    }

    modifier only_actor { require(isActor(msg.sender)); _; }
    modifier only_sender { require(sender() == msg.sender); _; }

    address[] public actors;
    mapping (address => bool) public confirmations;
    uint public timestampExpired;
}
