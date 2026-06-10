# NFT Ticketing

An NFT-based ticketing platform build for the IT4-Blockchain class 2026. 
Nour El Houda HACHEMI, Livia LEROY-STONE, Sara SERHAL, Raymond ZHENG

## How to use

When acessing the platform, the user can : 
1) Connect his/her MetaMask account ("Connect MetaMask" button at top right)
2) Create an event (with title, description and date, then "Create event" button)
3) Create one or more categories for that event (with title, description, price in wei, maximum supply and image, then 
button "Upload to IPFS and deploy category")
4) That event and category are now automatically selected, but the user can select others with the dropdown menus at 
the top of the page (if others have been created))
5) For the selected event and category, the user can buy tickets with metamask (Pay with wallet --> Buy with MetaMask) 
or by card (Card Payment --> Fake card number --> Simulate card payment)
6) When bought (and validated if bought with MetaMask), the number of tickets available diminishes by 1, the ticket 
bought becomes available (and is visualisable on Etherscan) and the contract revenue goes up (by the price of one ticket)
7) The user can withdraw the amount collected with ticket sales (at the bottom of the page, "Contract revenue" part, 
by "Withdraw funds") into their MetaMask account.

## Architecture

- `contracts/` : contracts, scripts and unit tests
- `api/` : API (FastAPI) (3-tier : presentation, domain, infrastructure)
- `frontend/` : React, Vite et Ethers.js
- `database` : SQLite

## Necessary installs 

 - Python 3.11 or higher
 - Node.js 24.16 or higher 
 - npm
 - Foundry
 - MetaMask (with Sepolia ETH)
 - MetaMask configurÃ© sur Sepolia
 - Pinata account and JWT with necessary permissions

## How to run

#### Specify .env file : 

Create .env file from example : 
```bash
cd contracts
cp .env.example .env
```

Fill in SEPOLIA_RPC_URL, SELLER_ADDRESS, PRIVATE_KEY and PINATA_JWT as specified. 

Leave TICKET_NFT_ADDRESS empty : the contracts are created from the user interface when the categories are added.


#### Run API 

Execute following code in a terminal :
```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

#### Run Frontend 

Execute following code in another terminal :
```bash
cd frontend
npm install
npm run dev
```

Then go to Localhost adress given : http://127.0.0.1:5173

## Tests

To run tests, execute following code : 

```bash
cd contracts && forge test
cd ../api && .venv/bin/python -m pytest
cd ../frontend && npm run lint && npm run build
```