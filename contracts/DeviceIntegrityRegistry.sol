// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DeviceIntegrityRegistry {
    mapping(address => bytes32) public deviceBaselines;
    mapping(address => bool) public deviceRegistered;
    
    mapping(address => bool) public approvedDevices;

    event IntegrityCheck(address indexed device, bytes32 indexed deviceHash, bool indexed matched, uint256 deviceData);
    event DeviceRegistered(address indexed device, bytes32 indexed baselineHash);

    constructor() {
        approvedDevices[0xC8277fc891E8d5E10FAB0C0166cD5F8cD890Cab7] = true;
        approvedDevices[0x41264776Cea5369556b86Dc01f26c2D6Ae797B61] = true;
    }

    function submitIntegrityCheck(bytes32 deviceHash, uint256 deviceData) public {
        require(approvedDevices[msg.sender], "Device not approved");
    
        // register the device with this hash as baseline (first transaction)
        if (!deviceRegistered[msg.sender]) {
            deviceBaselines[msg.sender] = deviceHash;
            deviceRegistered[msg.sender] = true;
            emit DeviceRegistered(msg.sender, deviceHash);
            emit IntegrityCheck(msg.sender, deviceHash, true, deviceData);
        } else {
            // check against stored baseline
            bool matched = (deviceHash == deviceBaselines[msg.sender]);
            emit IntegrityCheck(msg.sender, deviceHash, matched, deviceData);
        }
    }
}

