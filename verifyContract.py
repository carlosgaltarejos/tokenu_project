from web3 import Web3
from web3.middleware import geth_poa_middleware

def verify_contract():
    try:
        print("Conectando a la red Ethereum...")
        alchemy_url = 'https://eth-sepolia.g.alchemy.com/v2/GiExCFEkalG3rleHyqQBC7_F94XjSFN7'
        w3 = Web3(Web3.HTTPProvider(alchemy_url))

        if not w3.isConnected():
            print("No se pudo conectar a la red Ethereum")
            return

        print("Conexión a la red Ethereum exitosa")

        # Inject Geth PoA middleware
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        print("Configurando el contrato...")
        contract_address = '0x280725940d6444374ffcF50fa7D7bb9Eec8d0811'
        contract_abi = [
            {
                "inputs": [],
                "name": "name",
                "outputs": [
                    {
                        "internalType": "string",
                        "name": "",
                        "type": "string"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        checksum_address = Web3.toChecksumAddress(contract_address)
        contract = w3.eth.contract(address=checksum_address, abi=contract_abi)
        print("Contrato configurado exitosamente")

        print('Contract Version:', contract.functions.name().call())

        print("Llamando a la función 'name' del contrato...")
        contract_name = contract.functions.name().call()
        print(f"Nombre del contrato: {contract_name}")

    except Exception as e:
        print(f"Error llamando a la función 'name' del contrato: {str(e)}")

verify_contract()
