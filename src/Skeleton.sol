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
    /// Auto-incrementing id of the next token to mint (first token is 0).
    uint256 private _nextTokenId;
    /// Hard cap on the number of tickets this contract can ever mint.
    uint256 public immutable maxSupply;
    /// Price of ONE ticket, in wei.
    uint256 public price;
    /// Metadata URI shared by every ticket of this category (looks like ipfs://…).
    string public ticketURI;

    /**
     * EXERCISE 1 — Constructor
     *
     * Store `maxSupply_`, `ticketURI_` and `price_` in the state variables
     * above. (`name_` and `symbol_` are already forwarded to ERC721, and
     * the deployer is already set as owner via Ownable.)
     */
    constructor(
        string memory name_,
        string memory symbol_,
        uint256 maxSupply_,
        string memory ticketURI_,
        uint256 price_
    ) ERC721(name_, symbol_) Ownable(msg.sender) {
        // TODO: implement
    }

    /**
     * EXERCISE 3 — Public purchase
     *
     * Anyone can buy `quantity` tickets by paying exactly
     * `quantity × price` wei.
     *  - revert with "Incorrect ETH amount" when `msg.value` is wrong;
     *  - then delegate the minting to `_mintBatch`.
     */
    function buy(uint256 quantity) external payable returns (uint256[] memory) {
        // TODO: implement
    }

    /**
     * EXERCISE 4 — Platform mint
     *
     * The contract owner (the ticketing platform) can mint `quantity`
     * tickets to any address for free — used when the buyer pays by card.
     * Only the owner may call this (hint: a modifier from Ownable, look at
     * how `withdraw` is restricted). Delegate the minting to `_mintBatch`.
     */
    function mint(address to, uint256 quantity)
        external
        returns (uint256[] memory)
    {
        // TODO: implement (and add the missing modifier to the signature)
    }

    /**
     * EXERCISE 2 — Batch minting (shared by `buy` and `mint`)
     *
     * Mint `quantity` consecutive token ids to `to` and return them.
     *  - revert with "Quantity must be positive" when `quantity` is 0;
     *  - revert with "Sold out" when minting would exceed `maxSupply`;
     *  - for each token: take the next id, `_safeMint` it to `to`, and
     *    attach the category metadata with `_setTokenURI(tokenId, ticketURI)`.
     */
    function _mintBatch(address to, uint256 quantity)
        private
        returns (uint256[] memory)
    {
        // TODO: implement
    }

    /**
     * EXERCISE 5 — Withdraw proceeds
     *
     * Send the full ETH balance of the contract to the owner.
     *  - only the owner may call this;
     *  - revert with "Withdraw failed" when the transfer fails.
     * Hint: use a low-level `call{value: …}("") or transfer`.
     */
    function withdraw() external onlyOwner {
        // TODO: implement
    }

    /**
     * EXERCISE 6 — Enumerate someone's tickets
     *
     * Return every token id owned by `account`.
     * Hint: ERC721Enumerable gives you `balanceOf(account)` and
     * `tokenOfOwnerByIndex(account, i)`.
     */
    function ticketsOf(address account) external view returns (uint256[] memory) {
        // TODO: implement
    }

    // ------------------------------------------------------------------
    // Boilerplate — required because ERC721URIStorage and ERC721Enumerable
    // both extend ERC721, so Solidity needs explicit overrides.
    // Do not modify anything below this line.
    // ------------------------------------------------------------------

    function _update(address to, uint256 tokenId, address auth)
        internal
        override(ERC721, ERC721Enumerable)
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }

    function _increaseBalance(address account, uint128 value)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._increaseBalance(account, value);
    }

    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
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
