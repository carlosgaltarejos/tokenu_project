import requests
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.db import models
from rest_framework.views import APIView
from .models import FileToken
from .serializers import FileTokenSerializer
from web3 import Web3
from cryptography.fernet import Fernet
import os
import json
import base64
from django.core.files.base import ContentFile
from django.conf import settings
from django.http import JsonResponse


def home(request):
    return render(request, 'home.html')

def upload_file_form(request):
    return render(request, 'upload.html')
   
class TokenizeFileView(APIView):

    def post(self, request):
        file = request.FILES['file']
        blockchain = request.POST['blockchain']
        wallet_address = request.POST['wallet_address']
        encryption_key = request.POST['encryption_key']

        if file.size > 2 * 1024 * 1024:
            return JsonResponse({'error': 'File size exceeds 2MB'}, status=400)

        # Convertir la clave de encriptación proporcionada a una clave Fernet válida
        if len(encryption_key) < 32:
            encryption_key = encryption_key.ljust(32)
        elif len(encryption_key) > 32:
            encryption_key = encryption_key[:32]
        encryption_key = base64.urlsafe_b64encode(encryption_key.encode())

        # Encriptar el archivo sin leer su contenido
        fernet = Fernet(encryption_key)
        encrypted_content = fernet.encrypt(file.read())

        # Guardar el archivo encriptado en un nuevo archivo
        fs = FileSystemStorage()
        filename = fs.save(file.name, ContentFile(encrypted_content))
        file_url = fs.url(filename)
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        # Subir el archivo encriptado a IPFS
        token_uri = upload_to_ipfs(encrypted_content)

        # Tokenizar el archivo en la blockchain seleccionada
        if blockchain == 'ethereum':
            token_address = self.tokenize_ethereum(wallet_address, token_uri)
        elif blockchain == 'polygon':
            token_address = self.tokenize_polygon(wallet_address, token_uri)
        else:
            return JsonResponse({'error': 'Invalid blockchain selected'}, status=400)

        # Guardar la información del token en la base de datos
        file_token = FileToken.objects.create(
            file=filename,
            ethereum_token_address=token_address if blockchain == 'ethereum' else None,
            polygon_token_address=token_address if blockchain == 'polygon' else None
        )
        serializer = FileTokenSerializer(file_token)
        return JsonResponse(serializer.data, status=201)

    def tokenize_ethereum(self, wallet_address, token_uri):
        alchemy_url = settings.ETHEREUM_ALCHEMY_URL
        w3 = Web3(Web3.HTTPProvider(alchemy_url))

        # Verificar conexión
        if not w3.isConnected():
            raise ConnectionError(f"Failed to connect to Ethereum at {alchemy_url}")

        contract_address = Web3.toChecksumAddress(settings.ETHEREUM_CONTRACT_ADDRESS)
        contract_abi = settings.ETHEREUM_CONTRACT_ABI
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        account = Web3.toChecksumAddress(settings.ACCOUNT_ADDRESS)
        private_key = settings.PRIVATE_KEY
        nonce = w3.eth.get_transaction_count(account)

        wallet_address = Web3.toChecksumAddress(wallet_address)                                                       
        transaction = contract.functions.mint(wallet_address).buildTransaction({
            'chainId': 11155111,  # Chain ID for Sepolia
            'gas': 2000000,
            'gasPrice': w3.toWei('50', 'gwei'),
            'nonce': nonce
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt['status'] == 1:
            # Probar la llamada a otras funciones del contrato para verificar conectividad
            contract_name = contract.functions.name().call()
            print(f"Contract name: {contract_name}")

            try:
                token_id = contract.functions.tokenId().call() - 1
                token_address = contract.functions.ownerOf(token_id).call()
                return token_address
            except Exception as e:
                print(f"Error calling tokenId: {e}")
                raise Exception("Error calling tokenId")
        else:
            raise Exception("Token creation failed")

    def tokenize_polygon(self, wallet_address, token_uri):
        alchemy_url = settings.POLYGON_ALCHEMY_URL
        w3 = Web3(Web3.HTTPProvider(alchemy_url))

        # Verificar conexión
        if not w3.isConnected():
            raise ConnectionError(f"Failed to connect to Polygon at {alchemy_url}")

        contract_address = Web3.toChecksumAddress(settings.POLYGON_CONTRACT_ADDRESS)
        contract_abi = json.loads(settings.POLYGON_CONTRACT_ABI)
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        account = Web3.toChecksumAddress(settings.POLYGON_ACCOUNT)
        private_key = settings.POLYGON_PRIVATE_KEY
        nonce = w3.eth.get_transaction_count(account)

        wallet_address = Web3.toChecksumAddress(wallet_address)                                                     
        transaction = contract.functions.mint(wallet_address).buildTransaction({
            'chainId': 80001,  # Chain ID for Mumbai
            'gas': 2000000,
            'gasPrice': w3.toWei('50', 'gwei'),
            'nonce': nonce
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt['status'] == 1:
            token_id = contract.functions.tokenId().call() - 1
            token_address = contract.functions.ownerOf(token_id).call()
            return token_address
        else:
            raise Exception("Token creation failed")

def upload_to_ipfs(file_content):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "Authorization": f"Bearer {settings.PINATA_JWT}"
    }
    files = {
        'file': ('file', file_content)
    }
    response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        raise Exception(f"Failed to upload to IPFS: {response.text}")

    response_data = response.json()
    
    if "IpfsHash" not in response_data:
        raise KeyError(f"IpfsHash not found in response: {response_data}")
    
    ipfs_hash = response_data["IpfsHash"]
    return f"{settings.PINATA_GATEWAY}/ipfs/{ipfs_hash}"

def view_token_form(request):
    return render(request, 'view_token.html')

def show_wallet(request):
    wallet_address = request.GET.get('wallet_address')

    file_tokens = FileToken.objects.filter(
        models.Q(ethereum_token_address__isnull=False) |
        models.Q(polygon_token_address__isnull=False)
    )

    tokens = []
    for token in file_tokens:
        if token.ethereum_token_address:
            tokens.append({
                'blockchain': 'Ethereum',
                'token_address': token.ethereum_token_address,
                'file_name': token.file.name
            })
        if token.polygon_token_address:
            tokens.append({
                'blockchain': 'Polygon',
                'token_address': token.polygon_token_address,
                'file_name': token.file.name
            })

    return render(request, 'select_token.html', {'tokens': tokens})

def view_token(request):
    token_address = Web3.toChecksumAddress(request.POST.get('token_address'))
    encryption_key = request.POST.get('encryption_key')

    # Convertir la clave de encriptación proporcionada a una clave Fernet válida
    if len(encryption_key) < 32:
        encryption_key = encryption_key.ljust(32)
    elif len(encryption_key) > 32:
        encryption_key = encryption_key[:32]
    encryption_key = base64.urlsafe_b64encode(encryption_key.encode())

    file_token = get_object_or_404(FileToken, models.Q(ethereum_token_address=token_address) | models.Q(polygon_token_address=token_address))

    file_path = file_token.file.path

    # Leer y descifrar el contenido del archivo
    with open(file_path, 'rb') as f:
        encrypted_content = f.read()

    fernet = Fernet(encryption_key)
    try:
        decrypted_content = fernet.decrypt(encrypted_content)
    except:
        return HttpResponse("Invalid encryption key", status=400)

    response = HttpResponse(decrypted_content, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(file_path)
    return response

def verify_contract(request):
    try:
        # Step 1: Conectar a la red Ethereum
        print("Conectando a la red Ethereum...")
        alchemy_url = settings.ETHEREUM_ALCHEMY_URL
        w3 = Web3(Web3.HTTPProvider(alchemy_url))

        if not w3.isConnected():
            print("No se pudo conectar a la red Ethereum")
            return JsonResponse({'error': 'Failed to connect to Ethereum network'})
        print("Conexión a la red Ethereum exitosa")

        # Step 2: Configurar el contrato
        print("Configurando el contrato...")
        contract_address = settings.ETHEREUM_CONTRACT_ADDRESS
        contract_abi = settings.ETHEREUM_CONTRACT_ABI

        try:
            checksum_address = Web3.toChecksumAddress(contract_address)
            print(f"Dirección checksum: {checksum_address}")
        except Exception as e:
            print(f"Dirección del contrato inválida: {str(e)}")
            return JsonResponse({'error': f'Invalid contract address: {str(e)}'})

        try:
            contract = w3.eth.contract(address=checksum_address, abi=contract_abi)
            print("Contrato configurado exitosamente")
        except Exception as e:
            print(f"Error configurando el contrato: {str(e)}")
            return JsonResponse({'error': f'Error setting up contract: {str(e)}'})

        # Step 3: Llamar a la función 'name' del contrato usando eth_call manualmente
        try:
            print("Llamando a la función 'name' del contrato manualmente...")
            function_signature = w3.keccak(text='name()')[:4]
            call_data = function_signature.hex()
            print(f"call_data: {call_data}")

            call_transaction = {
                'to': checksum_address,
                'data': call_data,
            }
            result = w3.eth.call(call_transaction)
            print(f"Resultado de la llamada: {result}")
            if len(result) == 0:
                raise Exception("No data returned from the contract")

            contract_name = w3.codec.decode_abi(['string'], result)[0]
            print(f"Nombre del contrato: {contract_name}")
        except Exception as e:
            print(f"Error llamando a la función 'name' del contrato manualmente: {str(e)}")
            return JsonResponse({'error': f"Error llamando a la función 'name' del contrato manualmente: {str(e)}"})

        # Step 4: Llamar a la función 'symbol' del contrato
        try:
            print("Llamando a la función 'symbol' del contrato...")
            contract_symbol = contract.functions.symbol().call()
            print(f"Símbolo del contrato: {contract_symbol}")
        except Exception as e:
            print(f"Error llamando a la función 'symbol' del contrato: {str(e)}")
            return JsonResponse({'error': f"Error llamando a la función 'symbol' del contrato: {str(e)}"})

        # Step 5: Llamar a la función 'totalSupply' del contrato
        try:
            print("Llamando a la función 'totalSupply' del contrato...")
            total_supply = contract.functions.totalSupply().call()
            print(f"Suministro total del contrato: {total_supply}")
        except Exception as e:
            print(f"Error llamando a la función 'totalSupply' del contrato: {str(e)}")
            return JsonResponse({'error': f"Error llamando a la función 'totalSupply' del contrato: {str(e)}"})

        return JsonResponse({'message': 'Contract verification completed', 'contract_name': contract_name, 'contract_symbol': contract_symbol, 'total_supply': total_supply})

    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return JsonResponse({'error': str(e)})