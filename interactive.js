import { JsonRpcProvider, Wallet, parseEther, formatEther, hexlify, toUtf8Bytes } from "ethers";
import readline from "readline";

const provider = new JsonRpcProvider("http://127.0.0.1:7545");

// Active Ganache Account 0 Key
const PRIVATE_KEY = "0xe0f5c1f7b2b06992264236d0a8da3bc4fb5e2cd160faef7dc4eaf116983fb5a1";
const wallet = new Wallet(PRIVATE_KEY, provider);

// Edge Node Targets for Simulation
const NODES = {
  PI_NODE_01: "0xf19316e0132b92f037d1aee934fabbb45319fca4",
  PI_NODE_02: "0x5fbe75f6c9d3bff5b3410be1e1147992a056866a"
};

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function printHeader() {
  console.log("\n========================================================");
  console.log("   IoT Cybersecurity & Web3 Threat Monitor - Capstone   ");
  console.log("========================================================\n");
}

function showMenu() {
  console.log("\n--- MAIN CONTROL PANEL ---");
  console.log("1. Check Ganache Network State (Block Height & Gas)");
  console.log("2. Inspect Active Device Wallet (Address & ETH Balance)");
  console.log("3. Simulate Physical Tamper Alert (Low Severity - 0.001 ETH)");
  console.log("4. Simulate Network DDoS Intrusion (Critical Severity - 0.05 ETH)");
  console.log("5. Send Custom Encrypted Threat Data Payload (Data Hex Encoding)");
  console.log("6. Trigger Automated Stress Test (Batch 3 Threat Transactions)");
  console.log("7. Exit Demonstration");

  rl.question("\nSelect an action (1-7): ", async (choice) => {
    switch (choice.trim()) {
      case "1": {
        const block = await provider.getBlockNumber();
        const feeData = await provider.getFeeData();
        console.log(`\n[NETWORK STATUS]`);
        console.log(` Current Block Height : #${block}`);
        console.log(` Current Gas Price    : ${formatEther(feeData.gasPrice ?? 0n)} ETH`);
        break;
      }

      case "2": {
        const balance = await provider.getBalance(wallet.address);
        console.log(`\n[DEVICE WALLET]`);
        console.log(` Address : ${wallet.address}`);
        console.log(` Balance : ${formatEther(balance)} ETH`);
        break;
      }

      case "3": {
        console.log("\n[ALERT] Processing Physical Tamper Detection from Pi Node 01...");
        const tx = await wallet.sendTransaction({
          to: NODES.PI_NODE_01,
          value: parseEther("0.001"),
          data: hexlify(toUtf8Bytes("THREAT_TYPE: PHYSICAL_TAMPER"))
        });
        console.log(` -> Transaction Broadcasted! Hash: ${tx.hash}`);
        await tx.wait();
        console.log(" -> Block Mined & Confirmed on Ganache!");
        break;
      }

      case "4": {
        console.log("\n[CRITICAL ALERT] Processing High-Volume DDoS Intrusion from Pi Node 02...");
        const tx = await wallet.sendTransaction({
          to: NODES.PI_NODE_02,
          value: parseEther("0.05"),
          data: hexlify(toUtf8Bytes("THREAT_TYPE: NETWORK_DDOS_ATTACK"))
        });
        console.log(` -> Critical Threat Broadcasted! Hash: ${tx.hash}`);
        await tx.wait();
        console.log(" -> Block Mined & Confirmed on Ganache!");
        break;
      }

      case "5": {
        rl.question("\nEnter custom threat log payload text: ", async (customText) => {
          console.log(`\n[PAYLOAD] Encoding data: "${customText}"`);
          const hexData = hexlify(toUtf8Bytes(customText));
          const tx = await wallet.sendTransaction({
            to: NODES.PI_NODE_01,
            value: parseEther("0.0001"),
            data: hexData
          });
          console.log(` -> Payload Transaction Hash: ${tx.hash}`);
          await tx.wait();
          console.log(" -> Data Payload Permanently Anchored to Block!");
          showMenu();
        });
        return;
      }

      case "6": {
        console.log("\n[STRESS TEST] Initiating Batch Threat Simulation (3 Transactions)...");
        for (let i = 1; i <= 3; i++) {
          const tx = await wallet.sendTransaction({
            to: NODES.PI_NODE_01,
            value: parseEther("0.001"),
            data: hexlify(toUtf8Bytes(`BATCH_SIMULATION_SEQ_${i}`))
          });
          console.log(` [${i}/3] Sent! Hash: ${tx.hash}`);
          await tx.wait();
        }
        console.log(" -> Batch Threat Simulation Completed!");
        break;
      }

      case "7":
        console.log("\nTerminating IoT Threat Control Panel. Exiting...");
        rl.close();
        return;

      default:
        console.log("\n[ERROR] Invalid option selected. Please choose between 1 and 7.");
    }
    showMenu();
  });
}

printHeader();
showMenu();