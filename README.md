# CyperScope

1. start ganache workspace with this mnemonic (addresses and private key should be the same each time)
```
digital obvious endorse wave rain icon swamp amateur other broom bid happy
```
  - add ``truffle-config.js`` to ganache workspace projects
2. if needed add wallet addresses to approved addresses in the contract, creating the Proof of Authority
3. compile contract
```bash
truffle migrate --reset --network development
```
4. ``./rpi`` includes the files for the Raspberry Pi
  - if needed change ``PRIVATE_KEY`` in ``.env``
  - if needed change contract address to deployed address
5. if needed change contract address and run node js server
```bash
node web/server.js
```
6. dashboard at ``./web/index.html``

