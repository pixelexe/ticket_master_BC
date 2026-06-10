# NFT Ticketing

Application de billetterie NFT réalisée pour le cours Blockchain.

## Fonctionnalités

- création et consultation d'événements ;
- une catégorie de billets par contrat ERC-721 conforme à `Skeleton.sol` ;
- image et métadonnées stockées sur IPFS avec Pinata ;
- achat direct en SepoliaETH avec MetaMask ;
- faux paiement par carte, suivi d'un mint par l'API ;
- affichage des NFT possédés ;
- retrait des fonds par le vendeur.

## Architecture

- `contracts/` : contrats Solidity, tests et scripts Foundry ;
- `api/` : FastAPI en trois couches (`presentation`, `domain`, `infrastructure`) ;
- `frontend/` : React, Vite et Ethers.js ;
- SQLite pour les événements et catégories.

## Lancement

API :

```bash
cd api
source .venv/bin/activate
uvicorn app.main:app --reload
```

Frontend :

```bash
cd frontend
npm install
npm run dev
```

Swagger : http://127.0.0.1:8000/docs

Frontend : http://127.0.0.1:5173

## Tests

```bash
cd contracts && forge test
cd ../api && .venv/bin/python -m pytest
cd ../frontend && npm run lint && npm run build
```

## Configuration

Créer le fichier local de configuration à partir du modèle :

```bash
cd contracts
cp .env.example .env
```

Compléter ensuite `contracts/.env` :

```env
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com/
SELLER_ADDRESS=0xAdressePubliqueMetaMaskDuVendeur
TICKET_NFT_ADDRESS=0xAdresseDuContratDejaDeploye
PRIVATE_KEY=clePriveeDuWalletVendeur
PINATA_JWT=jwtPinata
```

Ce fichier est l'unique fichier `.env` du projet. L'API y lit les secrets et
fournit uniquement l'adresse publique du vendeur au frontend. Il ne faut donc
modifier aucune adresse dans `frontend/src/App.jsx`.

- `SEPOLIA_RPC_URL` : URL permettant à Forge et Web3.py d'accéder à Sepolia ;
- `SELLER_ADDRESS` : adresse publique MetaMask du vendeur ;
- `TICKET_NFT_ADDRESS` : contrat principal déjà déployé, peut rester vide avant le premier déploiement ;
- `PRIVATE_KEY` : clé du compte vendeur, utilisée par Forge et l'API pour signer ;
- `PINATA_JWT` : JWT créé dans Pinata, avec les droits d'upload de fichiers et JSON.

Le fichier `.env` est exclu de Git. Ne jamais publier la clé privée, le JWT Pinata ou envoyer une capture de ce fichier. Utiliser un wallet de développement dédié au testnet.

## Contrat Sepolia

L'adresse dépend du dernier contrat créé depuis l'interface Admin.
