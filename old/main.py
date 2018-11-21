import os
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

def compilar_contrato(file_path, solc_version):
    with open(file_path, 'r') as f:
        source = f.read()
    set_solc(solc_version)
    return compile_source(source)

def implantar_contrato(w3, interface_contrato):
    # Instanciar o contrato
    contrato = w3.eth.contract(
        abi=interface_contrato['abi'],
        bytecode=interface_contrato['bin'])

    # Envia a transação para implantar o contrato
    tx_hash = contrato.constructor().transact()

    # Aguarda a transação ser minerada e recebe o recibo da transação
    tx_recibo = w3.eth.getTransactionReceipt(tx_hash)
    return tx_recibo.contractAddress

def transact_func(w3, contrato, nome_func, args, check = False, show = False):
    gas_estimado = contrato.get_function_by_name(nome_func)(*args).estimateGas()
    if check:
        continuar = True if (input("\nGas estimado para a transação {}({}) é: {}. Continuar? [s]: ".format(nome_func, args, gas_estimado)) or 's').lower() == 's' else False
    if not check or continuar:
        print("Enviando transação para {}({})\n".format(nome_func, args))
        tx_hash = contrato.get_function_by_name(nome_func)(*args).transact()
        tx_recibo = w3.eth.waitForTransactionReceipt(tx_hash, 5)
        print("Recibo da transação minerado: \n")
        if show:
            pprint.pprint(dict(tx_recibo))
    else:
        print("Operação cancelada...")

def call_func(contrato, nome_func, args=[]):
    print("\nChamando a função {}({}):".format(nome_func, args))
    return contrato.get_function_by_name(nome_func)(*args).call()

def lista_funcoes(contrato):
    print('Funções disponiveis: {}\n'.format(contrato.all_functions()))

arquivo_contrato = input("Digite o caminho/nome do contrato [sol/greeter.sol]: ") or 'sol/greeter.sol'
versao_solc_contrato = input("Qual versão do solc deseja usar? [v0.4.24]: ") or 'v0.4.24'
compilado_solc = compilar_contrato(arquivo_contrato, versao_solc_contrato)
contrato_id, contrato_interface = compilado_solc.popitem()

# Conecta na rede Ethereum de testes
w3 = Web3(Web3.EthereumTesterProvider())
w3.eth.defaultAccount = w3.eth.accounts[0]

# Envia o contrato para rede
address = implantar_contrato(w3, contrato_interface)
print("Contrato {0} implatando. Endereço:: {1}\n".format(contrato_id, address))

# Crie uma instância do contrato com o endereço implantado
contrato = w3.eth.contract(address=address, abi=contrato_interface['abi'])



print('#### Saldação do contrato: {}\n'.format(call_func(contrato, 'greet')))

nome_func = input("Digite o nome da função [setGreeting]: ") or 'setGreeting'
nargs = int(input("Quantos argumentos para a função [1]: ") or 1)
args = []
for i in range(nargs):
    args.append(input("Argumento {} (Obrigatório): ".format(i)))

transact_func(w3, contrato, nome_func, args, True, True)

print('\n#### Saldação do contrato atualizada: {}\n'.format(contrato.functions.greet().call()))