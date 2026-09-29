# CyperScope

1. creat ganache workspace with this mnemonic (addresses and private keys should be the same each time)
```
digital obvious endorse wave rain icon swamp amateur other broom bid happy
```
  - add ``truffle-config.js`` to ganache workspace projects
  - change server hostname to ``10.42.0.1`` or Ethernet port IP address
2. if needed add wallet addresses to approved addresses in the contract, creating the Proof of Authority
3. compile contract
```bash
truffle migrate --reset --network development
```
4. ``./rpi`` includes the files for the Raspberry Pi
  - if needed change ``PRIVATE_KEY`` in ``.env``
  - if needed change contract address to deployed address
  - copy over required files to the Raspberry Pi
```bash
scp ./build/contracts/DeviceIntegrityRegistry.json ./rpi/cyberscope.py ./rpi/.env capstone@10.42.0.10:~/rpi/
```
5. if needed change contract address and run node js server
```bash
node web/server.js
```
6. dashboard at ``./web/index.html``

