# CyperScope

1. ``./rpi`` includes the files for the Raspberry Pi
  - change ``PRIVATE_KEY`` in ``.env``
2. add wallet addresses to approved addresses in the contract, creating the Proof of Authority
3. compile contract

```bash
truffle migrate --reset --network development
```

4. run node js server

```bash
node server.js
```

5. dashboard at ``./web/index.html``

