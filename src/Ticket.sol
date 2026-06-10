// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../lib/openzeppelin-contracts-upgradeable/lib/openzeppelin-contracts/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "../lib/openzeppelin-contracts-upgradeable/lib/openzeppelin-contracts/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "../lib/openzeppelin-contracts-upgradeable/lib/openzeppelin-contracts/contracts/access/Ownable.sol";

/**
 * Contract part - NFT
 *
 * Each ticket category of an event is one ERC-721 contract. Tickets are
 * either bought directly with ETH (`buy`) or minted for free by the
 * platform that owns the contract (`mint`, e.g. after a card payment).
 *
 * Complete the exercises marked TODO below, in order.
 */
contract Ticket is ERC721URIStorage, ERC721Enumerable, Ownable {
    uint256 private _nextTokenId;
    uint256 public immutable maxSupply;
    uint256 public price;
    string public ticketURI;

    constructor(
        string memory name_,
        string memory symbol_,
        uint256 maxSupply_,
        string memory ticketURI_,
        uint256 price_
    ) ERC721(name_, symbol_) Ownable(msg.sender) {
        maxSupply = maxSupply_;
        ticketURI = ticketURI_;
        price = price_;
    }

    function buy(uint256 quantity) external payable returns (uint256[] memory) {
        require(msg.value == quantity * price, "Incorrect ETH amount");
        return _mintBatch(msg.sender, quantity);
    }

    function mint(address to, uint256 quantity) external onlyOwner returns (uint256[] memory) {
        return _mintBatch(to, quantity);
    }

    function _mintBatch(address to, uint256 quantity) private returns (uint256[] memory tokenIds) {
        require(quantity > 0, "Quantity must be positive");
        require(_nextTokenId + quantity <= maxSupply, "Sold out");

        tokenIds = new uint256[](quantity);
        for (uint256 i = 0; i < quantity; i++) {
            uint256 tokenId = _nextTokenId;
            _nextTokenId++;
            tokenIds[i] = tokenId;
            _safeMint(to, tokenId);
            _setTokenURI(tokenId, ticketURI);
        }
    }

    function withdraw() external onlyOwner {
        (bool success,) = payable(owner()).call{value: address(this).balance}("");
        require(success, "Withdraw failed");
    }

    function ticketsOf(address account) external view returns (uint256[] memory tokenIds) {
        uint256 balance = balanceOf(account);
        tokenIds = new uint256[](balance);

        for (uint256 i = 0; i < balance; i++) {
            tokenIds[i] = tokenOfOwnerByIndex(account, i);
        }
    }

    function remainingSupply() external view returns (uint256) {
        return maxSupply - _nextTokenId;
    }

    function _update(address to, uint256 tokenId, address auth)
        internal
        override(ERC721, ERC721Enumerable)
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }

    function _increaseBalance(address account, uint128 value) internal override(ERC721, ERC721Enumerable) {
        super._increaseBalance(account, value);
    }

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721Enumerable, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}