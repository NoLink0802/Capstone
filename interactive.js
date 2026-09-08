import { JsonRpcProvider, Wallet, parseEther } from "ethers";
import readline from "readline";

const provider = new JsonRpcProvider("http://127.0.0.1:7545");
// Account 0
const wallet = new Wallet("0xa96d0ddbc871e814ffaf753757b24ee43ef63f3ae6900f4c46c77db41461f781", provider);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log("\n==========================================");
console.log("  IoT Threat Detection - Interactive CLI  ");
console.log("==========================================\n");

function showMenu() {
  console.log("\nSelect an action:");
  console.log("1. Check Ganache Block Number");
  console.log("2. Check Device Wallet Balance");
  console.log("3. Simulate Anomaly Threat Event (Send Transaction)");
  console.log("4. Exit");
  
  rl.question("\nEnter choice (1-4): ", async (choice) => {
    switch (choice.trim()) {
      case "1": {
        const block = await provider.getBlockNumber();
        console.log(`\n Current Block Number: ${block}`);
        break;
      }
      case "2": {
        const balance = await provider.getBalance(wallet.address);
        console.log(`\n Wallet Balance: ${balance} ETH`);
        break;
      }
      case "3": {
        console.log("\n Sending threat detection payload to blockchain...");
        const tx = await wallet.sendTransaction({
          to: "0x8AB99a47BAaac2E257D35026eaC187e4184576B8",
          value: parseEther("0.1")
        });
        console.log(` Transaction Sent! Hash: ${tx.hash}`);
        await tx.wait();
        console.log(" Block Mined & Confirmed on Ganache!");
        break;
      }
      case "4":
        console.log("Exiting...");
        rl.close();
        return;
      default:
        console.log("Invalid option, try again.");
    }
    showMenu();
  });
}

showMenu();