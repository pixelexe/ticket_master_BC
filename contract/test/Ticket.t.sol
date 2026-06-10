// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import "../lib/openzeppelin-contracts-upgradeable/lib/openzeppelin-contracts/contracts/access/Ownable.sol";
import {Ticket} from "../src/Ticket.sol";

contract TicketTest is Test {
    Ticket private ticket;

    address private buyer = makeAddr("buyer");
    address private secondBuyer = makeAddr("secondBuyer");

    uint256 private constant PRICE = 0.01 ether;
    uint256 private constant MAX_SUPPLY = 3;
    string private constant TICKET_URI = "ipfs://metadata-cid";

    function setUp() public {
        ticket = new Ticket("Concert VIP", "VIP", MAX_SUPPLY, TICKET_URI, PRICE);
        vm.deal(buyer, 1 ether);
        vm.deal(secondBuyer, 1 ether);
    }

    function test_ConstructorStoresCategoryData() public view {
        assertEq(ticket.name(), "Concert VIP");
        assertEq(ticket.symbol(), "VIP");
        assertEq(ticket.maxSupply(), MAX_SUPPLY);
        assertEq(ticket.ticketURI(), TICKET_URI);
        assertEq(ticket.price(), PRICE);
        assertEq(ticket.owner(), address(this));
    }

    function test_BuyMintsRequestedQuantityAndStoresPayment() public {
        vm.prank(buyer);
        uint256[] memory tokenIds = ticket.buy{value: 2 * PRICE}(2);

        assertEq(tokenIds.length, 2);
        assertEq(tokenIds[0], 0);
        assertEq(tokenIds[1], 1);
        assertEq(ticket.ownerOf(0), buyer);
        assertEq(ticket.ownerOf(1), buyer);
        assertEq(ticket.tokenURI(0), TICKET_URI);
        assertEq(address(ticket).balance, 2 * PRICE);
    }

    function test_BuyRevertsWhenPaymentIsIncorrect() public {
        vm.prank(buyer);
        vm.expectRevert(bytes("Incorrect ETH amount"));
        ticket.buy{value: PRICE}(2);
    }

    function test_BuyRevertsWhenQuantityIsZero() public {
        vm.prank(buyer);
        vm.expectRevert(bytes("Quantity must be positive"));
        ticket.buy(0);
    }

    function test_MintAllowsOwnerToMintBatchAfterCardPayment() public {
        uint256[] memory tokenIds = ticket.mint(buyer, 2);

        assertEq(tokenIds.length, 2);
        assertEq(ticket.balanceOf(buyer), 2);
        assertEq(address(ticket).balance, 0);
    }

    function test_MintRevertsForNonOwner() public {
        vm.prank(buyer);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, buyer));
        ticket.mint(buyer, 1);
    }

    function test_MintRevertsWhenSoldOut() public {
        ticket.mint(buyer, 2);

        vm.expectRevert(bytes("Sold out"));
        ticket.mint(secondBuyer, 2);
    }

    function test_TicketsOfReturnsOwnedTokenIds() public {
        ticket.mint(buyer, 2);

        uint256[] memory tokenIds = ticket.ticketsOf(buyer);

        assertEq(tokenIds.length, 2);
        assertEq(tokenIds[0], 0);
        assertEq(tokenIds[1], 1);
    }

    function test_WithdrawTransfersAllFundsToOwner() public {
        vm.prank(buyer);
        ticket.buy{value: PRICE}(1);
        uint256 ownerBalanceBefore = address(this).balance;

        ticket.withdraw();

        assertEq(address(this).balance, ownerBalanceBefore + PRICE);
        assertEq(address(ticket).balance, 0);
    }

    receive() external payable {}
}
