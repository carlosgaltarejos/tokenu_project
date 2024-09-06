from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
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
from django.db import models
import requests
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

def upload_file_form(request):
    return render(request, 'upload.html')

def view_token_form(request):
    return render(request, 'view_token.html')

def show_wallet(request):
    wallet_address = Web3.toChecksumAddress(request.GET.get('wallet_address'))

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
    print("Entrando a la función view_token")  # Debugging
    try:
        # Obtener el token_id, la clave de encriptación y la blockchain desde la solicitud
        token_id = int(request.POST.get('token_id'))
        encryption_key = request.POST.get('encryption_key')
        blockchain = request.POST.get('blockchain')

        print(f"Token ID: {token_id}, Encryption Key: {encryption_key}, Blockchain: {blockchain}")  # Debugging

        # Verificar que los campos no estén vacíos
        if token_id is None or encryption_key == '' or blockchain == '':
            return JsonResponse({'error': 'token_id, clave de encriptación y blockchain son requeridos'}, status=400)

        # Obtener el contrato adecuado para la blockchain seleccionada
        try:
            w3, contract, _ = get_blockchain_data(blockchain)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        # Obtener el token URI desde el contrato
        try:
            token_uri = contract.functions.tokenURI(token_id).call()
            print(f"Token URI: {token_uri}")
        except Exception as e:
            return JsonResponse({'error': f'No se pudo obtener el tokenURI: {str(e)}'}, status=400)

        # Verificar si el token_uri es una URL completa o un hash
        if token_uri.startswith("http://") or token_uri.startswith("https://"):
            ipfs_url = token_uri
            ipfs_hash = token_uri.split("/")[-1]  # Construir el hash desde la URL
        else:
            ipfs_hash = token_uri.replace("ipfs://", "")
            ipfs_url = f"{settings.PINATA_GATEWAY}/ipfs/{ipfs_hash}"

        print(f"IPFS URL: {ipfs_url}")
        response = requests.get(ipfs_url)

        # Si la respuesta del primer gateway no es satisfactoria, intentar con otro gateway
        if response.status_code != 200:
            print("Fallo en el primer gateway, intentando con https://ipfs.io/ipfs/")
            ipfs_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
            response = requests.get(ipfs_url)

            print(f"IPFS Response Status Code (from fallback): {response.status_code}")
            if response.status_code != 200:
                return JsonResponse({'error': 'Error al descargar el archivo desde IPFS con ambos gateways'}, status=400)

        encrypted_content = response.content

        # Convertir la clave de encriptación proporcionada a una clave Fernet válida
        encryption_key = encryption_key.ljust(32)[:32]
        encryption_key = base64.urlsafe_b64encode(encryption_key.encode())

        fernet = Fernet(encryption_key)
        try:
            decrypted_content = fernet.decrypt(encrypted_content)
        except Exception as e:
            return JsonResponse({'error': f'Clave de encriptación inválida: {str(e)}'}, status=400)

        response = HttpResponse(decrypted_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="decrypted_file"'
        return response

    except Exception as e:
        return JsonResponse({'error': f'Error procesando la solicitud: {str(e)}'}, status=500)

    
def verify_contract(request):
    try:
        if not w3.isConnected():
            return JsonResponse({'error': 'No se pudo conectar a la red Ethereum'})

        # Llamar a la función 'name' del contrato
        contract_name = contract.functions.name().call()

        # Llamar a la función 'symbol' del contrato
        contract_symbol = contract.functions.symbol().call()

        return JsonResponse({
            'message': 'Verificación del contrato completada',
            'contract_name': contract_name,
            'contract_symbol': contract_symbol,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)})


# Función para conectar a una blockchain
def get_blockchain_data(blockchain):
    if blockchain == 'sepolia':
        alchemy_url = settings.ETHEREUM_ALCHEMY_URL
        contract_address = Web3.toChecksumAddress(settings.ETHEREUM_CONTRACT_ADDRESS)
        contract_abi = settings.ETHEREUM_CONTRACT_ABI
        chain_id = 11155111  # Chain ID para Sepolia
    elif blockchain == 'polygon':
        alchemy_url = settings.POLYGON_ALCHEMY_URL
        contract_address = Web3.toChecksumAddress(settings.POLYGON_CONTRACT_ADDRESS)
        contract_abi = settings.POLYGON_CONTRACT_ABI
        chain_id = 80001  # Chain ID para Mumbai (Polygon testnet)
    else:
        raise ValueError('Blockchain seleccionada no es válida')

    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    return w3, contract, chain_id

class TokenizeFileView(APIView):
    print("Entrando a la función TokenizeFileView...")  # Debugging 
    def post(self, request):
        logger.info("Iniciando el proceso de tokenización...")
        logger.info(f"Datos recibidos: {request.POST}")

        try:
            file = request.FILES['file']
            encryption_key = request.POST['encryption_key']
            wallet_address = Web3.toChecksumAddress(request.POST['wallet_address'])
            blockchain = request.POST['blockchain']

            logger.info(f"Blockchain seleccionada: {blockchain}")
            logger.info(f"Dirección de la wallet: {wallet_address}")

            if file.size > 2 * 1024 * 1024:
                logger.warning("El archivo excede los 2MB")
                return JsonResponse({'error': 'El tamaño del archivo excede los 2MB'}, status=400)

            # Convertir la clave de encriptación proporcionada a una clave Fernet válida
            encryption_key = base64.urlsafe_b64encode(encryption_key.ljust(32)[:32].encode())
            fernet = Fernet(encryption_key)
            encrypted_content = fernet.encrypt(file.read())

            # Guardar el archivo encriptado en un nuevo archivo
            fs = FileSystemStorage()
            filename = fs.save(file.name, ContentFile(encrypted_content))
            file_url = fs.url(filename)
            logger.info(f"Archivo encriptado guardado en: {file_url}")

            # Subir el archivo encriptado a IPFS
            token_uri = upload_to_ipfs(encrypted_content)
            logger.info(f"Archivo subido a IPFS con URI: {token_uri}")

            # Preparar la transacción según la blockchain seleccionada
            if blockchain == 'sepolia':
                chain_id = 11155111  # Sepolia
                contract_address = Web3.toChecksumAddress(settings.ETHEREUM_CONTRACT_ADDRESS)
                contract_abi = settings.ETHEREUM_CONTRACT_ABI
                logger.info("Usando la red Sepolia")
            elif blockchain == 'polygon':
                chain_id = 80001  # Polygon Mumbai
                contract_address = Web3.toChecksumAddress(settings.POLYGON_CONTRACT_ADDRESS)
                contract_abi = settings.POLYGON_CONTRACT_ABI
                logger.info("Usando la red Polygon")
            else:
                logger.error(f"Blockchain seleccionada no es válida: {blockchain}")
                return JsonResponse({'error': 'Blockchain no válida'}, status=400)

            w3 = Web3(Web3.HTTPProvider(settings.POLYGON_ALCHEMY_URL if blockchain == 'polygon' else settings.ETHEREUM_ALCHEMY_URL))
            contract = w3.eth.contract(address=contract_address, abi=contract_abi)

            # Preparar la transacción para mintear el NFT
            transaction = contract.functions.safeMint(wallet_address, token_uri).buildTransaction({
                'chainId': chain_id,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(wallet_address)
            })

            logger.info(f"Transacción preparada: {transaction}")

            return JsonResponse({
                'contract_address': contract_address,
                'transaction_data': transaction['data'],
                'token_uri': token_uri,
            }, status=201)

        except Exception as e:
            logger.error(f"Error durante la tokenización: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

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
        raise Exception(f"Error al subir a IPFS: {response.text}")

    response_data = response.json()
    
    if "IpfsHash" not in response_data:
        raise KeyError(f"IpfsHash no encontrado en la respuesta: {response_data}")
    
    ipfs_hash = response_data["IpfsHash"]
    return f"{settings.PINATA_GATEWAY}/ipfs/{ipfs_hash}"
