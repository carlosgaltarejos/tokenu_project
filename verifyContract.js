const { ethers } = require('ethers');

// Configuración de Alchemy
const ALCHEMY_API_KEY = 'GiExCFEkalG3rleHyqQBC7_F94XjSFN7';
const ALCHEMY_URL = `https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}`;

(async () => {
  try {
    // Conectar al proveedor de Alchemy
    const provider = new ethers.providers.JsonRpcProvider(ALCHEMY_URL);
    console.log('Conexión a la red Ethereum exitosa');

    // Dirección del contrato
    const contractAddress = '0x280725940d6444374ffcF50fa7D7bb9Eec8d0811';

    // ABI del contrato
    const contractABI = [
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
      // ... incluye otros métodos del ABI que necesites
    ];

    // Crear una instancia del contrato
    const contract = new ethers.Contract(contractAddress, contractABI, provider);

    // Llamar a la función 'name'
    const name = await contract.name();
    console.log(`Nombre del contrato: ${name}`);
  } catch (error) {
    console.error(`Error verificando el contrato: ${error.message}`);
  }
})();









