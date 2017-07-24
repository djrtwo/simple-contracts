import pytest
import time


ESCROW_EXPIRATION = int(time.time()) + 10000
ESCROW_AMOUNT = 10000000 # larger than gas cost to pull it out


@pytest.fixture()
def escrow_actors(accounts):
    # start at one so coinbase doesn't interfere with balances
    return accounts[1:4]


@pytest.fixture()
def escrow_expiration():
    return ESCROW_EXPIRATION


@pytest.fixture()
def escrow_arguments(accounts):
    return {
        '_sender': accounts[1],
        '_recipient': accounts[2],
        '_arbitrator': accounts[3],
        '_timestampExpired': escrow_expiration(),
    }


@pytest.fixture()
def escrow_contract(provider, accounts):
    args = escrow_arguments(accounts)
    transaction = {"value": ESCROW_AMOUNT}
    escrow, _ = provider.get_or_deploy_contract('Escrow', transaction, deploy_kwargs=args)
    return escrow


@pytest.fixture()
def expired_escrow_contract(web3, provider, accounts):
    args = escrow_arguments(accounts)
    # a bit hacky -- timestamp of blocks seems disconnected from computer timestamp..
    args['_timestampExpired'] = int(web3.eth.getBlock('latest')['timestamp']) + 12

    transaction = {"value": ESCROW_AMOUNT}
    escrow, _ = provider.get_or_deploy_contract('Escrow', transaction, deploy_kwargs=args)
    return escrow


def test_escrow_init(web3, escrow_contract, escrow_arguments):
    sender = escrow_contract.call().sender()
    recipient = escrow_contract.call().recipient()
    arbitrator = escrow_contract.call().arbitrator()
    timestampExpired = escrow_contract.call().timestampExpired()

    assert sender == escrow_arguments['_sender']
    assert recipient == escrow_arguments['_recipient']
    assert arbitrator == escrow_arguments['_arbitrator']
    assert timestampExpired == escrow_arguments['_timestampExpired']
    assert web3.eth.getBalance(escrow_contract.address) == ESCROW_AMOUNT


def test_is_actor(accounts, escrow_contract, escrow_actors):
    for actor in escrow_actors:
        assert escrow_contract.call().isActor(actor)

    assert not escrow_contract.call().isActor(accounts[-1])


def test_confirmations_init_state(escrow_contract, escrow_actors):
    # initialized to no confirmations
    for actor in escrow_actors:
        has_actor_confirmed = escrow_contract.call().confirmations(actor)
        assert not has_actor_confirmed

    assert not escrow_contract.call().isConfirmed()


def test_confirm_confirmations(chain, escrow_contract, escrow_actors):
    for actor in escrow_actors:
        assert not escrow_contract.call().confirmations(actor)
        transact = escrow_contract.transact({"from": actor})
        confirm_txn_hash = transact.confirm()
        chain.wait.for_receipt(confirm_txn_hash)
        assert escrow_contract.call().confirmations(actor)


def test_confirm_is_confirmed(chain, escrow_contract, escrow_arguments):
    sender = escrow_arguments['_sender']
    transact = escrow_contract.transact({"from": sender})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)

    assert not escrow_contract.call().isConfirmed()

    recipient = escrow_arguments['_recipient']
    transact = escrow_contract.transact({"from": recipient})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)

    assert escrow_contract.call().isConfirmed()


def test_confirm_by_arbitrator(chain, escrow_contract, escrow_arguments):
    arbitrator = escrow_arguments['_arbitrator']
    transact = escrow_contract.transact({"from": arbitrator})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)

    assert not escrow_contract.call().isConfirmed()

    recipient = escrow_arguments['_recipient']
    transact = escrow_contract.transact({"from": recipient})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)

    assert escrow_contract.call().isConfirmed()


def test_confirm_transfer(chain, escrow_contract, escrow_arguments):
    web3 = chain.web3

    recipient = escrow_arguments['_recipient']
    initial_balance = web3.eth.getBalance(recipient)
    escrow_balance = web3.eth.getBalance(escrow_contract.address)
    assert escrow_balance > 0

    # confirmation 1
    sender = escrow_arguments['_sender']
    transact = escrow_contract.transact({"from": sender})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)

    one_conf_balance = web3.eth.getBalance(recipient)
    assert one_conf_balance == initial_balance

    # confirmation 2
    arbitrator = escrow_arguments['_arbitrator']
    transact = escrow_contract.transact({"from": arbitrator})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)

    after_balance = web3.eth.getBalance(recipient)
    assert after_balance - initial_balance == escrow_balance

    after_escrow_balance = web3.eth.getBalance(escrow_contract.address)
    assert after_escrow_balance == 0


def test_void_by_sender(chain, expired_escrow_contract):
    web3 = chain.web3

    sender = expired_escrow_contract.call().sender()
    initial_balance = web3.eth.getBalance(sender)

    initial_escrow_balance = web3.eth.getBalance(expired_escrow_contract.address)
    assert initial_escrow_balance > 0

    void_txn_hash = expired_escrow_contract.transact({"from": sender}).void()
    chain.wait.for_receipt(void_txn_hash)

    final_balance = web3.eth.getBalance(sender)
    final_escrow_balance = web3.eth.getBalance(expired_escrow_contract.address)

    assert final_escrow_balance == 0
    # assume fees to pull out escrow cost less than a 10th of escrow amount
    assert final_balance - initial_balance > ESCROW_AMOUNT - (ESCROW_AMOUNT / 10)


def test_void_not_expired(escrow_contract):
    sender = escrow_contract.call().sender()

    with pytest.raises(Exception):
        # raises TransactionFailed
        # is specific class only in ethereum/tester.pytest
        # so test only looks for Exception
        escrow_contract.transact({"from": sender}).void()


def test_void_by_non_sender(accounts, expired_escrow_contract):
    recipient = expired_escrow_contract.call().recipient()
    arbitrator = expired_escrow_contract.call().arbitrator()
    non_actor = accounts[-1]

    test_cannot_void = [recipient, arbitrator, non_actor]
    for account in test_cannot_void:
        with pytest.raises(Exception):
            # raises TransactionFailed
            # is specific class only in ethereum/tester.pytest
            # so test only looks for Exception
            expired_escrow_contract.transact({"from": account}).void()

