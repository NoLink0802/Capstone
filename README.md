# CyberScope

1. create ganache workspace with this mnemonic (addresses and private keys should be the same each time)
   ```
   digital obvious endorse wave rain icon swamp amateur other broom bid happy
   ```
   - add ``truffle-config.js`` to the ganache workspaces' projects
   - change server hostname to ``10.42.0.1`` or Ethernet port IP address
2. start contract
   - _if mnemonic is different, or if needed add wallet addresses to approved addresses in the contract, creating the Proof of Authority_
   - build contract
   ```bash
   truffle migrate --reset --network development
   ```
3. ``./rpi`` includes the files for the Raspberry Pi
   - _if the mnemonic is different from above, update private key_
   - _if contract or mnemonic is changed, update contract address to the deployed address_
   - copy over required files to the Raspberry Pi
   ```bash
   scp ./build/contracts/DeviceIntegrityRegistry.json ./rpi/cyberscope.py capstone@10.42.0.10:~/rpi/
   ```
4. start server
   - _if contract or mnemonic is changed, update contract address to the deployed address_
   - run Node.js
   ```bash
   cd web
   node server.js
   ```
5. on Raspberry Pi start CyberScope
   ```bash
   cd rpi
   ./venv/bin/python cyberscope.py
   ```
6. view dashboard at ``./web/index.html``

