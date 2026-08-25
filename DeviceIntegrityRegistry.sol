// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title DeviceIntegrityRegistry
 * @dev Stores IoT baseline hashes and logs tamper/anomaly events on-chain.
 */
contract DeviceIntegrityRegistry {
    enum DeviceStatus { SECURE, TAMPERED, RESOURCE_ANOMALY, NETWORK_ANOMALY }

    struct DeviceState {
        bytes32 baselineHash;
        bytes32 lastReportedHash;
        DeviceStatus status;
        uint256 lastUpdated;
        uint256 anomalyCount;
    }

    mapping(string => DeviceState) public devices;
    address public owner;

    event DeviceRegistered(string indexed deviceId, bytes32 baselineHash);
    event AnomalyFlagged(string indexed deviceId, DeviceStatus status, string reason, uint256 timestamp);
    event IntegrityChecked(string indexed deviceId, bool passed, DeviceStatus status);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function registerDevice(string memory deviceId, bytes32 baselineHash) public onlyOwner {
        devices[deviceId] = DeviceState({
            baselineHash: baselineHash,
            lastReportedHash: baselineHash,
            status: DeviceStatus.SECURE,
            lastUpdated: block.timestamp,
            anomalyCount: 0
        });

        emit DeviceRegistered(deviceId, baselineHash);
    }

    function submitStateCheck(
        string memory deviceId,
        bytes32 currentHash,
        uint8 statusCode,
        string memory reason
    ) public returns (bool) {
        DeviceState storage dev = devices[deviceId];
        require(dev.baselineHash != bytes32(0), "Device not registered");

        dev.lastReportedHash = currentHash;
        dev.lastUpdated = block.timestamp;

        if (currentHash != dev.baselineHash || statusCode != 0) {
            dev.status = DeviceStatus(statusCode == 0 ? uint8(DeviceStatus.TAMPERED) : statusCode);
            dev.anomalyCount += 1;
            emit AnomalyFlagged(deviceId, dev.status, reason, block.timestamp);
            emit IntegrityChecked(deviceId, false, dev.status);
            return false;
        }

        dev.status = DeviceStatus.SECURE;
        emit IntegrityChecked(deviceId, true, DeviceStatus.SECURE);
        return true;
    }
}
