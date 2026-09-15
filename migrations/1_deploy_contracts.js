const DeviceIntegrityRegistry = artifacts.require("DeviceIntegrityRegistry");

module.exports = function(deployer) {
  deployer.deploy(DeviceIntegrityRegistry);
};
