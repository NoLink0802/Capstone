import express from "express";
import { JsonRpcProvider, parseEther, formatEther, hexlify, toUtf8Bytes, getAddress } from "ethers";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const provider = new JsonRpcProvider("http://127.0.0.1:7545");

// Dynamic Wallet Initialization
let wallet;

async function getActiveSigner() {
  if (!wallet) {
    const signer = await provider.getSigner(0);
    wallet = signer;
  }
  return wallet;
}

const NODES = {
  PI_NODE_01: getAddress("0xcbcfe4535f1bc88bdf7dfe8838aadabf64e1f878"),
  PI_NODE_02: getAddress("0x5fbe75f6c9d3bff5b3410be1e1147992a056866a")
};

// 1. Get Network State
app.get("/api/network-state", async (req, res) => {
  try {
    const block = await provider.getBlockNumber();
    const feeData = await provider.getFeeData();
    res.json({
      blockHeight: block,
      gasPrice: formatEther(feeData.gasPrice ?? 0n)
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 2. Inspect Active Wallet
app.get("/api/wallet-info", async (req, res) => {
  try {
    const signer = await getActiveSigner();
    const address = await signer.getAddress();
    const balance = await provider.getBalance(address);
    res.json({
      address: address,
      balance: formatEther(balance)
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3, 4, 5. Send Threat / Custom Payload
app.post("/api/send-threat", async (req, res) => {
  try {
    const signer = await getActiveSigner();
    const { targetNode, payloadText, valueEth } = req.body;
    const targetAddress = NODES[targetNode] || getAddress(targetNode);
    
    const tx = await signer.sendTransaction({
      to: targetAddress,
      value: valueEth ? parseEther(valueEth) : 0n,
      data: hexlify(toUtf8Bytes(payloadText)),
      gasLimit: 100000
    });
    
    await tx.wait();
    res.json({ success: true, txHash: tx.hash });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 6. Stress Test Batch
app.post("/api/stress-test", async (req, res) => {
  try {
    const signer = await getActiveSigner();
    const hashes = [];
    for (let i = 1; i <= 3; i++) {
      const tx = await signer.sendTransaction({
        to: NODES.PI_NODE_01,
        data: hexlify(toUtf8Bytes(`BATCH_SIMULATION_SEQ_${i}`)),
        gasLimit: 100000
      });
      await tx.wait();
      hashes.push(tx.hash);
    }
    res.json({ success: true, hashes });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(3000, async () => {
  try {
    const signer = await getActiveSigner();
    const addr = await signer.getAddress();
    console.log(`Web Dashboard running at http://localhost:3000`);
    console.log(`Connected to Ganache Account: ${addr}`);
  } catch (err) {
    console.log("Web Dashboard running at http://localhost:3000 (Ganache Offline)");
  }
});
