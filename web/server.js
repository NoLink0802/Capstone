const express = require("express");
const { ethers } = require("ethers");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

// Blockchain configuration
const CONTRACT_ADDRESS = "0x2a362E8346FEAF0A7D5923fb0792aE11367b1080";
const RPC_URL = "HTTP://10.42.0.1:7545";
const ARTIFACT_PATH = path.join(__dirname, "../build/contracts/DeviceIntegrityRegistry.json");
const CACHE_DURATION = 10000; // 10 seconds in milliseconds

// State
let devicesCache = {};
let lastUpdateTime = 0;
let provider;
let contract;

// Initialize provider and contract
async function initializeContract() {
  try {
    provider = new ethers.JsonRpcProvider(RPC_URL);
    const artifact = JSON.parse(fs.readFileSync(ARTIFACT_PATH, "utf-8"));
    contract = new ethers.Contract(CONTRACT_ADDRESS, artifact.abi, provider);
    console.log("Contract initialized successfully");
  } catch (error) {
    console.error("Error initializing contract:", error);
    process.exit(1);
  }
}

// Fetch block timestamp from blockchain
async function getBlockTimestamp(blockNumber) {
  try {
    const block = await provider.getBlock(blockNumber);
    return block ? new Date(block.timestamp * 1000).toISOString() : null;
  } catch (error) {
    console.error(`Error fetching block ${blockNumber}:`, error);
    return null;
  }
}

// Update device data from blockchain
async function updateDeviceData() {
  try {
    const now = Date.now();
    
    // Only update if cache is stale
    if (now - lastUpdateTime < CACHE_DURATION) {
      return devicesCache;
    }

    console.log("Fetching device data from blockchain...");
    
    const newDevices = {};

    // Get all DeviceRegistered events (all devices ever registered)
    const deviceEvents = await contract.queryFilter("DeviceRegistered");
    
    // Get all IntegrityCheck events
    const integrityEvents = await contract.queryFilter("IntegrityCheck");

    // Build device map from registration events
    for (const event of deviceEvents) {
      const deviceAddress = event.args.device;
      const baselineHash = event.args.baselineHash;

      newDevices[deviceAddress] = {
        address: deviceAddress,
        data: null,
        baselineHash: baselineHash,
        verified: null, // Will be updated from integrity checks
        lastCheckTime: null
      };
    }

    // Sort integrity events by block number (oldest first) to get latest check per device
    integrityEvents.sort((a, b) => a.blockNumber - b.blockNumber);

    for (const event of integrityEvents) {
      const deviceAddress = event.args.device;
      const matched = event.args.matched;
      const deviceData = event.args.deviceData;

      if (deviceAddress && newDevices[deviceAddress]) {
        newDevices[deviceAddress].verified = matched;
        newDevices[deviceAddress].data = deviceData;
        
        // Fetch actual block timestamp
        const timestamp = await getBlockTimestamp(event.blockNumber);
        newDevices[deviceAddress].lastCheckTime = timestamp;
      }
    }

    devicesCache = newDevices;
    lastUpdateTime = now;
    console.log(`Updated ${Object.keys(newDevices).length} devices from blockchain`);

    return newDevices;

  } catch (error) {
    console.error("Error fetching device data:", error);
    return devicesCache; // Return cached data if fetch fails
  }
}

// API endpoint: Get all devices
app.get("/api/devices", async (req, res) => {
  try {
    const devices = await updateDeviceData();
    res.json(devices);
  } catch (error) {
    console.error("Error in /api/devices:", error);
    res.status(500).json({ error: "Failed to fetch devices" });
  }
});

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({ status: "Server is running" });
});

// Start server
initializeContract().then(() => {
  app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
});

