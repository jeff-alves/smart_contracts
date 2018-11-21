from time import sleep

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
        if show:
            print("Recibo da transação minerado: \n")
            pprint.pprint(dict(tx_recibo))
        print('Finalizado.')
    else:
        print("Operação cancelada...")

def call_func(contrato, nome_func, args=[]):
    print("\nChamando a função {}({}):".format(nome_func, args))
    return contrato.get_function_by_name(nome_func)(*args).call()

def lista_funcoes(contrato):
    print('Funções disponiveis:\n')
    print("\n".join([x.fn_name for x in contrato.all_functions()]))

def lista_accounts(w3):
    print('Contas disponiveis:')
    print("\n".join(w3.eth.accounts))

def set_account_address(w3, address):
    global user_address
    user_address = address
    w3.eth.defaultAccount = address

def clear():
    os.system('clear')

def menu_principal():
    global w3, user_address, arquivo_contrato, versao_solc_contrato, compilado_solc, contrato_id, contrato_interface, contrato_address, contrato

    clear()
    print("\n\tSmart Contracts - Segurança em Redes\n")
    if w3 and user_address:
        print('1 - Listar usuarios disponiveis')
        print('2 - Setar usuario')
        print('3 - Carregar contrato solc')
        print('4 - Implantar contrato carregado')
        print('5 - Instanciar contrato implantado')
        print('6 - Listar funções do contrato')
        print('7 - Call contrato')
        print('8 - Transact contrato')
        escolha = input("\n>>> ")
        if escolha == '1':
            clear()
            lista_accounts(w3)
            input("\nPressione enter para continuar")
        elif escolha == '2':
            clear()
            a = input("\nQual conta deseja usar? [{}]".format(w3.eth.accounts[0])) or w3.eth.accounts[0]
            set_account_address(w3, a)
        elif escolha == '3':
            clear()
            arquivo_contrato = input("Digite o caminho/nome do contrato [sol/presenca.sol]: ") or 'sol/presenca.sol'
            versao_solc_contrato = input("Qual versão do solc deseja usar? [v0.4.24]: ") or 'v0.4.24'
            compilado_solc = compilar_contrato(arquivo_contrato, versao_solc_contrato)
            contrato_id, contrato_interface = compilado_solc.popitem()
            input("Contrato Compilado.\nPressione enter para continuar")
        elif escolha == '4':
            clear()
            if contrato_id and contrato_interface:
                contrato_address = implantar_contrato(w3, contrato_interface)
                print("Contrato {0} implatando. Endereço: {1}\n".format(contrato_id, contrato_address))
                input("Pressione enter para continuar")
            else:
                input("Carregue um contrato antes!\nPressione enter para continuar")
        elif escolha == '5':
            clear()
            if contrato_address:
                contrato = w3.eth.contract(address=contrato_address, abi=contrato_interface['abi'])
                print("Contrato {0} Instanciado.\n".format(contrato_id))
                input("Pressione enter para continuar")
            else:
                input("Faça a implantação de um contrato primeiro!\nPressione enter para continuar")
        elif escolha == '6':
            clear()
            if contrato:
                lista_funcoes(contrato)
                input("\nPressione enter para continuar")
            else:
                input("Carregue uma instancia do contrato primeiro!\nPressione enter para continuar")
        elif escolha == '7':
            clear()
            if contrato:
                nome_func = input("Digite o nome da função: ")
                nargs = int(input("Quantos argumentos para a função [0]: ") or 0)
                args = []
                for i in range(nargs):
                    args.append(input("Argumento {}: ".format(i + 1)))
                if nome_func:
                    print('Retorno da função: ', call_func(contrato, nome_func, args))
                else:
                    print('Nome da função obrigatório')
                input("\nPressione enter para continuar")
            else:
                input("Carregue uma instancia do contrato primeiro!\nPressione enter para continuar")
        elif escolha == '8':
            clear()
            if contrato:
                nome_func = input("Digite o nome da função: ")
                nargs = int(input("Quantos argumentos para a função [0]: ") or 0)
                args = []
                for i in range(nargs):
                    args.append(input("Argumento {}: ".format(i+1)))
                if nome_func:
                    transact_func(w3, contrato, nome_func, args, True, True)
                else:
                    print('Nome da função obrigatório')
                input("\nPressione enter para continuar")
            else:
                input("Carregue uma instancia do contrato primeiro!\nPressione enter para continuar")
    else:
        print('1 - Conectar a rede Ethereum')
        print('2 - Listar usuarios disponiveis')
        print('3 - Setar usuario')
        escolha = input("\n>>> ")
        if escolha == '1':
            clear()
            w3 = Web3(Web3.EthereumTesterProvider())
            print("Conectado a rede Ethereum de testes\n")
            input("\nPressione enter para continuar")
        elif escolha == '2':
            clear()
            lista_accounts(w3)
            input("\nPressione enter para continuar")
        elif escolha == '3':
            clear()
            a = input("\nQual conta deseja usar? [{}]".format(w3.eth.accounts[0])) or w3.eth.accounts[0]
            set_account_address(w3, a)


w3 = None
user_address = None
arquivo_contrato = None
versao_solc_contrato = None
compilado_solc = None
contrato_id = None
contrato_interface = None
contrato_address = None
contrato = None
def main():
    while True:
        try:
            menu_principal()
        except Exception as exc:
            print(str(exc))
            input("\nPressione enter para continuar")

main()