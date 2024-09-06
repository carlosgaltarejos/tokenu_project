# TokenU Project - Plataforma de Tokenización en Blockchain

TokenU es una plataforma que permite la tokenización de archivos en la blockchain utilizando Ethereum (Sepolia) y Polygon (Mumbai). El sistema tokeniza archivos cargados por el usuario, encriptándolos y almacenándolos de manera segura en **IPFS** (InterPlanetary File System), y luego crea un **NFT** (Token No Fungible) asociado al archivo. Los usuarios también pueden consultar y descargar archivos previamente tokenizados utilizando su **ID** de token y una clave de encriptación.

## Funcionalidades Principales

### 1. **Tokenización de archivos**
- **Subida de Archivos**: Los usuarios pueden cargar archivos desde sus dispositivos locales.
- **Encriptación**: Los archivos son encriptados utilizando una clave de encriptación proporcionada por el usuario.
- **Almacenamiento en IPFS**: Una vez encriptado, el archivo se almacena en **IPFS** a través de la API de **Pinata**.
- **Creación de NFT**: El sistema genera un **NFT** en la blockchain seleccionada (Ethereum o Polygon), que queda asociado con el archivo encriptado.

### 2. **Consulta y visualización de NFTs**
- **Consulta de Archivos**: Los usuarios pueden introducir el **ID** del token, la **clave de encriptación**, y seleccionar la blockchain para recuperar un archivo tokenizado.
- **Desencriptación y Descarga**: Si se proporciona la clave correcta, el archivo es desencriptado y devuelto al usuario como un archivo descargable.

## Tecnologías utilizadas

### Backend
- **Django**: Framework de Python para construir la API que gestiona la lógica de tokenización y visualización de archivos.
- **Web3.py**: Biblioteca para interactuar con la blockchain de Ethereum y Polygon.
- **Cryptography (Fernet)**: Librería utilizada para encriptar y desencriptar los archivos cargados por el usuario.
- **Pinata**: Servicio de pinning para subir y gestionar archivos en IPFS.
- **Alchemy**: Gateway utilizado para interactuar con las blockchains de Ethereum y Polygon.

### Frontend
- **HTML/CSS**: La interfaz de usuario está construida utilizando HTML y Bootstrap para un diseño responsive y moderno.
- **JavaScript (Web3.js)**: Para conectar la wallet MetaMask del usuario con la blockchain, y firmar las transacciones.

### Blockchain
- **Ethereum (Sepolia)** y **Polygon (Mumbai)**: Blockchains utilizadas para crear y gestionar los NFTs.
- **MetaMask**: Wallet utilizada para interactuar con las blockchains y firmar transacciones.

## Configuración y ejecución local

### Requisitos Previos
- **Python 3.8+**
- **Node.js** (para frontend)
- **MetaMask** instalado en tu navegador.

### Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/tokenu.git
cd tokenu
```

### Backend (Django)
1. Crea y activa un entorno virtual:
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
env\Scripts\activate      # Windows
```

2. Instala las dependencias del proyecto:
```bash
pip install -r requirements.txt
```

3. Configura las variables de entorno en un archivo `.env`:
```bash
# Ethereum (Sepolia)
ETHEREUM_ALCHEMY_URL=https://eth-sepolia.alchemyapi.io/v2/tu-api-key
ETHEREUM_CONTRACT_ADDRESS=0xTuContratoSepolia

# Polygon (Mumbai)
POLYGON_ALCHEMY_URL=https://polygon-mumbai.g.alchemy.com/v2/tu-api-key
POLYGON_CONTRACT_ADDRESS=0xTuContratoPolygon

# Pinata API
PINATA_JWT=Bearer tu-token-pinata
```

4. Ejecuta las migraciones de la base de datos y el servidor:
```bash
python manage.py migrate
python manage.py runserver
```

### Frontend (Interfaz)
El frontend está basado en formularios HTML básicos. No requiere un entorno de desarrollo específico más allá de **Node.js** para manejar dependencias. Asegúrate de tener **MetaMask** instalado en tu navegador y que estés conectado a la red **Sepolia** o **Mumbai**.

## Uso de Remix para Deploy de contratos

El proyecto incluye contratos inteligentes que deben ser desplegados en **Ethereum Sepolia** y **Polygon Mumbai** a través de **Remix**. Sigue estos pasos:

1. Accede a **Remix IDE**: [Remix](https://remix.ethereum.org/)
2. Carga el contrato en Remix y compílalo.
3. Conecta tu wallet MetaMask a la red **Sepolia** o **Mumbai** y despliega el contrato.
4. Copia la dirección del contrato y actualiza las variables de entorno del proyecto en `.env`.

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas agregar nuevas funcionalidades o mejorar el código, por favor abre un **issue** o realiza un **pull request**.

---
