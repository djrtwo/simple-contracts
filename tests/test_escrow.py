import pytest
import time


ESCROW_EXPIRATION = int(time.time()) + 10000


@pytest.fixture()
def escrow_actors(accounts):
    return accounts[0:3]


@pytest.fixture()
def escrow_expiration():
    return ESCROW_EXPIRATION


@pytest.fixture()
def escrow_arguments(accounts):
    return {
        '_sender': accounts[0],
        '_recipient': accounts[1],
        '_arbitrator': accounts[2],
        '_timestampExpired': escrow_expiration(),
    }


@pytest.fixture()
def escrow_contract(chain, accounts):
    escrow, _ = chain.provider.get_or_deploy_contract('Escrow', {}, [], escrow_arguments(accounts))
    return escrow


def test_escrow_init(escrow_contract, escrow_arguments):
    sender = escrow_contract.call().sender()
    recipient = escrow_contract.call().recipient()
    arbitrator = escrow_contract.call().arbitrator()
    timestampExpired = escrow_contract.call().timestampExpired()

    assert sender == escrow_arguments['_sender']
    assert recipient == escrow_arguments['_recipient']
    assert arbitrator == escrow_arguments['_arbitrator']
    assert timestampExpired == escrow_arguments['_timestampExpired']


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
    # confirmation 1
    sender = escrow_arguments['_sender']
    transact = escrow_contract.transact({"from": sender})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)

    # confirmation 2
    arbitrator = escrow_arguments['_arbitrator']
    transact = escrow_contract.transact({"from": arbitrator})
    confirm_txn_hash = transact.confirm()
    chain.wait.for_receipt(confirm_txn_hash)



# def test_custom_greeting(chain):
    # greeter, _ = chain.provider.get_or_deploy_contract('Greeter')

    # set_txn_hash = greeter.transact().setGreeting('Guten Tag')
    # chain.wait.for_receipt(set_txn_hash)

    # greeting = greeter.call().greet()
    # assert greeting == 'Guten Tag'
