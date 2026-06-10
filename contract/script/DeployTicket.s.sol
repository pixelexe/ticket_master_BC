// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {Ticket} from "../src/Ticket.sol";

contract DeployTicket is Script {
    function run() external returns (Ticket ticket) {
        vm.startBroadcast();
        ticket = new Ticket(
            "Concert VIP", "VIP", 100, "ipfs://bafkreiggmlo5m5xhsdcsppgm5vpirivv4zzowznr77vjxtuoybetnaoigi", 0.01 ether
        );
        vm.stopBroadcast();

        console.log("Ticket deployed at:", address(ticket));
    }
}
