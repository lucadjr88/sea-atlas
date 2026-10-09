# Primo avvio

Prerequisiti: Node 20+, npm, pm2 (`npm i -g pm2`). File necessari: `rpc-pool-complete.json` (in questa cartella) e `/home/luca/sly/SLY_7.36mio.js` (solo per estrarre le IDL).

## 1. Installa le dipendenze del server

```bash
cd /home/luca/sea/server
npm install
```

## 2. Estrai le IDL da sly.js

Serve solo la prima volta o quando sly.js cambia versione. Crea `server/idl/sage.json` e `server/idl/profile.json`.

```bash
node extract-idl.js
```

## 3. Verifica la lettura delle flotte

Stampa in JSON le flotte del `playerProfileId` impostato in `server/config.js`.

```bash
node fleets.js
```

## 4. Esegui i test del client

```bash
cd /home/luca/sea/client
npm test
```

## 5. Avvio in primo piano (prova)

```bash
cd /home/luca/sea/server
node server.js
```

Apri `http://localhost:3000`. Altri endpoint: `http://localhost:3000/fleets` (snapshot JSON) e `ws://localhost:3000/ws`.
Ferma con `Ctrl+C`.

## 6. Avvio permanente con pm2

```bash
cd /home/luca/sea/server
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

`pm2 startup` stampa un comando con `sudo`: eseguilo a mano per l'avvio al boot.

## Gestione quotidiana

```bash
pm2 status
pm2 logs sea-server
pm2 restart sea-server
pm2 stop sea-server
```

## Configurazione

- `server/config.js`: porta (3000), `playerProfileId`, program id SAGE, percorso della pool RPC.
- `rpc-pool-complete.json`: pool di endpoint RPC (contiene chiavi API: non pubblicarlo).
- `server/server.js`: intervallo di aggiornamento (`POLL_MS`, 30 s).

## Problemi comuni

- `403 Firewall rule violation`: la chiave Ironforge di sly funziona solo nel browser di Star Atlas; il server usa la pool.
- `[pool] <nome> fallito`: l'endpoint va in pausa e il server prova il successivo.
- Porta occupata: `lsof -i :3000`, oppure cambia `port` in `server/config.js`.
- Pagina senza flotte: controlla `curl localhost:3000/fleets` (campo `error`).
