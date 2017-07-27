pragma solidity ^0.4.11;

// v0.0.1
// Author(s): Danny Ryan

// Contract in Alpha. For educational purposes only
// Currently entirely **UNTESTED**

// # Trust Fund Contract #
// Involves two 'actors' -- 'trustmaker' and 'beneficiary
// Holds Ether from 'trustmaker' to be transferred to 'beneficiary'.
// Distribution schedule is initialized at contract creation as a set of
// [timestamp, percentage] where each timestamp dictates a certain percentage 
// of the funds to be allowed to distributed on or after said timestamp.
// The percentages of all timestamps must sum to 100.

// Ether in contract is transferred to 'beneficiary' upon successul calls to `withdraw`
// Ether can only be withdrawn by 'beneficiary' once contract is instantiated

contract TrustFund {
    /*
        holds a timestamp and associated percentage (integer less than or equal to 100)
        at 'timestamp' an additional 'percentage' percentage of the funds can be released
    */
    struct Payout {
        uint timestamp;
        uint percentage;
    }

    function TrustFund(address _beneficiary, uint[] timestamps, uint[] percentages) payable {
        require(msg.value);

        beneficiary = _beneficiary;
        initialBalance = msg.value;
        _initalizePayoutSchedule(timestamps, percentages);
    }

    function withdraw(uint amount) only_beneficiary when_payout_allowed(amount) {
        assert(beneficiary().call.value(amount)());
    }

    function _initalizePayoutSchedule(uint[] timestamps, uint[] percentages) internal {
        require(timestamps.length > 0);
        require(percentages.length > 0);
        require(timestamps.length == percentages.length)

        uint totalPayout = 0;
        for (uint i = 0; i < timestamps.length; i++) {
            payouts.push(Payout(timestamps[i], percentages[i]));
            totalPayout += percentages[i];
        }

        assert(totalPayout == 100);
    }

    function percentageAllowed(uint timestamp) constant (uint) {
        payoutPercentage = 0;
        for (uint i = 0 ; i < payouts.length; i++) {
            if (now >= payouts[i].timestamp) {
                payoutPercentage += payouts[i].percentage;
            }
        }

        return payoutPercentage;
    }

    function availableForWithdrawal(uint timestamp) constant (uint) {
        uint percentageWithdrawn = ((initialBalance - this.balance) * 100) / initialBalance;
        uint availablePercentage = percentageAllowed(timestamp) - percentageWithdrawn;

        return (initialBalance * availablePercentage) / 100
    }

    modifier only_beneficiary { require(beneficiary == msg.sender); _; }
    modifier when_payout_allowed(uint amount) { 
        require(amount >= availableForWithdrawal(now));
        _;
    }

    address public beneficiary;
    uint public initialBalance;
    Payout[] public payouts;
}
