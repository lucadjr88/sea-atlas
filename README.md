# Flotte Star Atlas

Mappa isometrica in sola lettura delle flotte Star Atlas. Il server Node legge i dati da Solana e il client Phaser visualizza posizioni, rotte e stati delle flotte.

## Requisiti

- Node.js 20 o superiore
- npm

## Configurazione

Copia `rpc-pool-complete.example.json` in `rpc-pool-complete.json` nella root del progetto. Il file reale e' escluso da Git: inserisci li' i tuoi endpoint RPC e non pubblicare chiavi API.

## Avvio

```sh
cd server
npm install
node server.js
```

Apri `http://localhost:3000`.

## Test client

```sh
cd client
npm test
```
