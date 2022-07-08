import logging

from web3.providers.eth_tester import EthereumTesterProvider
from web3 import Web3
from eth_tester import PyEVMBackend
from solcx import compile_source
import solcx


solcx.install_solc(version='0.8.9')
solcx.set_solc_version('0.8.9')


def compile_source_file(file_path):
    with open(file_path, 'r') as f:
        source = f.read()

    return compile_source(source)


w3 = Web3(EthereumTesterProvider(PyEVMBackend()))

compiled_sol = compile_source_file('contracts/users_manager.sol')

contract_id, contract_interface = compiled_sol.popitem()

tx_hash = w3.eth.contract(
    abi=contract_interface['abi'],
    bytecode=contract_interface['bin']).constructor().transact()

address = w3.eth.get_transaction_receipt(tx_hash)['contractAddress']

logging.debug(f'Contract {contract_id} deployed to: {address}')

users_manager_contract = w3.eth.contract(address=address, abi=contract_interface["abi"])


def register_user_on_blockchain(user_id, username):

    gas_estimate = users_manager_contract.functions.notifyUserCreated(user_id, username).estimate_gas()

    if gas_estimate < 100000:
        tx_hash = users_manager_contract.functions.notifyUserCreated(user_id, username).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        logging.info(f'User registration status: {receipt["status"]}')
    else:
        logging.info("Gas cost exceeds 100000")


if __name__ == '__main__':
    register_user_on_blockchain(1, "n")
