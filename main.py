import os
import time
import pprint

from web3 import Web3
from solc import compile_source, install_solc

def set_solc(version):
    solc_path = os.path.join(os.path.expanduser("~"), '.py-solc/solc-' + version + '/bin')
    if not os.path.isdir(solc_path):
        install_solc(version)

    os_path = os.environ["PATH"].split(':')
    if solc_path not in os_path:
        os_path = list(filter(lambda x: '.py-solc/solc-' not in x, os_path))
        os_path.append(solc_path)
        os.environ["PATH"] = ':'.join(os_path)

def compile_source_file(file_path, solc_version):
    with open(file_path, 'r') as f:
        source = f.read()
    set_solc(solc_version)
    return compile_source(source)

def deploy_contract(w3, contract_interface):
    # Instantiate and deploy contract
    contrato = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin'])

    # Submit the transaction that deploys the contract
    tx_hash = contrato.constructor().transact()

    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    address = tx_receipt.contractAddress

    return address


def wait_for_receipt(w3, tx_hash, poll_interval):
   while True:
       tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
       if tx_receipt:
         return tx_receipt
       time.sleep(poll_interval)


contract_path = input("Digite o caminho/nome do contrato [sol/greeter.sol]: ") or 'sol/greeter.sol'
contract_solc_v = input("Qual versão do solc deseja usar? [v0.4.24]: ") or 'v0.4.24'
compiled_sol = compile_source_file(contract_path, contract_solc_v)
contract_id, contract_interface = compiled_sol.popitem()

w3 = Web3(Web3.EthereumTesterProvider())
w3.eth.defaultAccount = w3.eth.accounts[0]


address = deploy_contract(w3, contract_interface)
print("Deployed {0} to: {1}\n".format(contract_id, address))

# Create the contract instance with the newly-deployed address
contr = w3.eth.contract( address=address, abi=contract_interface['abi'])

# Display the default greeting from the contract
print('#### Default contract greeting: {}\n'.format(contr.functions.greet().call()))

print('Contract functions: ', contr.all_functions(), '\n')

function_name = input("Digite o nome da função [setGreeting]: ") or 'setGreeting'
nargs = int(input("Quantos argumentos para a função [1]: ") or 1)
args = []
for i in range(nargs):
    args.append(input("Argumento {} (Obrigatório): ".format(i)))

gas_estimate = contr.get_function_by_name(function_name)(*args).estimateGas()

print("\nGas estimate to transact with {}({}): {}".format(function_name,args, gas_estimate))
continuar = True if (input("Continuar? [s]: ") or 's').lower() == 's' else False

if continuar:
  print("Sending transaction to {}({})\n".format(function_name,args))
  tx_hash = contr.get_function_by_name(function_name)(*args).transact()
  receipt = wait_for_receipt(w3, tx_hash, 1)
  print("Transaction receipt mined: \n")
  pprint.pprint(dict(receipt))
else:
  print("Operação cancelada...")


# Display the new greeting value
print('\n#### Updated contract greeting: {}\n'.format(contr.functions.greet().call()))