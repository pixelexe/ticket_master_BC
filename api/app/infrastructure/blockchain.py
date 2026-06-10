import json
from pathlib import Path

from web3 import Web3
from web3.logs import DISCARD

from app.domain.events import BlockchainDeploymentError, TicketMintError


class Web3TicketContractDeployer:
    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        seller_address: str,
        artifact_path: Path,
    ):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.web3.eth.account.from_key(private_key)
        self.seller_address = Web3.to_checksum_address(seller_address)

        if self.account.address != self.seller_address:
            raise ValueError("PRIVATE_KEY does not match SELLER_ADDRESS")

        artifact = json.loads(artifact_path.read_text())
        self.contract_factory = self.web3.eth.contract(
            abi=artifact["abi"],
            bytecode=artifact["bytecode"]["object"],
        )
        self.contract_abi = artifact["abi"]

    def deploy(
        self,
        name: str,
        symbol: str,
        price_wei: int,
        max_supply: int,
        metadata_uri: str,
    ) -> str:
        try:
            transaction = self.contract_factory.constructor(
                name,
                symbol,
                max_supply,
                metadata_uri,
                price_wei,
            ).build_transaction(
                {
                    "from": self.seller_address,
                    "nonce": self.web3.eth.get_transaction_count(
                        self.seller_address, "pending"
                    ),
                    "chainId": self.web3.eth.chain_id,
                }
            )
            signed_transaction = self.account.sign_transaction(transaction)
            transaction_hash = self.web3.eth.send_raw_transaction(
                signed_transaction.raw_transaction
            )
            receipt = self.web3.eth.wait_for_transaction_receipt(
                transaction_hash,
                timeout=180,
            )
        except Exception as error:
            raise BlockchainDeploymentError(
                "Ticket contract deployment failed"
            ) from error

        if receipt["status"] != 1 or receipt["contractAddress"] is None:
            raise BlockchainDeploymentError("Ticket contract deployment reverted")

        return Web3.to_checksum_address(receipt["contractAddress"])

    def mint_for(
        self,
        contract_address: str,
        buyer_address: str,
    ) -> tuple[int, str]:
        try:
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=self.contract_abi,
            )
            transaction = contract.functions.mint(
                Web3.to_checksum_address(buyer_address),
                1,
            ).build_transaction(
                {
                    "from": self.seller_address,
                    "nonce": self.web3.eth.get_transaction_count(
                        self.seller_address, "pending"
                    ),
                    "chainId": self.web3.eth.chain_id,
                }
            )
            signed_transaction = self.account.sign_transaction(transaction)
            transaction_hash = self.web3.eth.send_raw_transaction(
                signed_transaction.raw_transaction
            )
            receipt = self.web3.eth.wait_for_transaction_receipt(
                transaction_hash,
                timeout=180,
            )
            events = contract.events.Transfer().process_receipt(
                receipt,
                errors=DISCARD,
            )
        except Exception as error:
            raise TicketMintError("Ticket mint failed") from error

        if receipt["status"] != 1 or not events:
            raise TicketMintError("Ticket mint reverted")

        return events[0]["args"]["tokenId"], transaction_hash.hex()
