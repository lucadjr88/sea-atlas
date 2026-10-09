# Piano di realizzazione

Obiettivo intermedio: visualizzazione **sola lettura** delle flotte Star Atlas che si muovono su una mappa 2D isometrica (stile Caesar 3), usando sly.js.

## Architettura

```
Solana RPC ──> sly.js (Node) ──> snapshot flotte (JSON) ──> client Phaser ──> render mappa/navi
```

- **Backend sottile (Node)**: usa sly.js per leggere le flotte e le espone al client (REST/WebSocket). Tiene la chiave RPC fuori dal browser e fa da cache.
- **Client (Phaser, cartella `demo/`)**: nessuna logica on-chain, riceve solo snapshot normalizzati.

## Fasi

### 0. Ricognizione sly.js (workspace indicizzato)
- Individuare le funzioni per: elenco flotte (per owner/profilo o globale), stato flotta (Idle, MoveWarp, MoveSubwarp, Mining, Respawn, StarbaseLoadingBay…), posizione/settore, rotta (origine, destinazione, tempi di partenza/arrivo), dati nave (tipo, nome).
- Verificare se è possibile leggere tutte le flotte di un settore senza conoscere gli owner (es. `getProgramAccounts` con filtri).
- Output: tabella "dato necessario → funzione sly.js".

### 1. Script di lettura dati (Node)
- Script CLI che stampa le flotte di un wallet/profilo in JSON.
- Definire lo **schema normalizzato**: `{id, nome, shipType, stato, settore:[x,y], da:[x,y], a:[x,y], tPartenza, tArrivo}`.
- Gestione RPC: endpoint configurabile, rate limit, retry.

### 2. Server di snapshot
- Endpoint `/fleets` (polling) o WebSocket; cache con refresh ogni N secondi.
- Possibile sottoscrizione agli account (`onAccountChange`) in seguito.

### 3. Mappa nel client
- Coordinate Star Atlas (settori, griglia 2D con x,y interi) → coordinate schermo isometriche.
- Sfondo/griglia dei settori, camera con pan/zoom, etichette.
- Solo le basi stellari/pianeti principali come punti di interesse (dati statici da sly.js o JSON).

### 4. Flotte sulla mappa
- Sprite per nave (per ora quelli in `demo/assets/ships`, mappatura tipo → sprite).
- Sprite a 8 direzioni in base al vettore di movimento.
- Flotte in movimento: interpolazione lineare tra `da` e `a` usando `tPartenza`/`tArrivo` (posizione calcolata dal tempo, non dal polling → movimento fluido).
- Flotte ferme: posizione = settore corrente / base.

### 5. Interazione in sola lettura
- Click su flotta → pannello con nome, stato, rotta, ETA.
- Filtri (owner, stato) e ricerca.

### 6. Rifinitura
- Gestione errori/disconnessione RPC, indicatore "ultimo aggiornamento".
- Prestazioni con molte flotte (culling, pooling sprite).

## Decisioni prese
1. Flotte: solo quelle del proprio wallet/profilo (nessuna scansione globale, `getProgramAccounts` non necessario).
2. Rete: mainnet, con RPC dedicato configurato via variabile d'ambiente.
3. Backend: server Node sempre attivo (processo perenne) con polling + cache e WebSocket verso il client.
4. Resa: isometrica fin da subito (proiezione 2D settore → schermo nel client).

## Identificativi (solo chiavi pubbliche, sola lettura)
- walletPublicKey: `GeUiZvjERgN95MFxU5wogLWPRUUpMgzQzdQnvyBkQHxv`
- authority: `9ynTDJrA8EHqmSskLdooeptY7z4U4qrDUT1uQjEqKVJY`
- playerProfileId: `4PsiXxqZZkRynC96UMZDQ6yDuMTWB1zmn4hr84vQwaz8`

## Risultati fase 0 (sorgente: `/home/luca/sly/SLY_7.36mio.js`)

sly.js è uno userscript Tampermonkey (browser, `GM.*`, `BrowserAnchor`): **non è importabile in Node**. Va riusata la logica, non il file. Serve `@solana/web3.js` + `@coral-xyz/anchor` in Node, con le IDL `sageIDL`/`profileIDL` (righe 427-428, minificate: estrarle con uno script, non aprirle).

| Dato | Come lo fa sly | Riga |
|---|---|---|
| Flotte possedute | `sageProgram.account.fleet.all([memcmp offset 41 = playerProfileId])` | ~8000 |
| Flotte in prestito | stesso, `memcmp offset 105` | ~8007 |
| Nome flotta | `fleet.account.fleetLabel` (bytes UTF-8, rimuovere `\0`) | ~8018 |
| Stato e posizione | `getFleetState(accountInfo, fleet)`: decodifica dal byte 439 dei dati dell'account flotta | 927 |
| Stati | 0 StarbaseLoadingBay, 1 Idle (`sector`), 2 MineAsteroid, 3 MoveWarp, 4 MoveSubwarp, 5 Respawn, 6 StarbaseUpgrade, 7 ReadyToExitWarp | 927-980 |
| Fine movimento | MoveWarp: `warpFinish`; MoveSubwarp: `arrivalTime` (secondi) | 5294-5295 |
| Settore/starbase da coordinate | `getSectorFromCoords`, `getStarbaseFromCoords` (memcmp 41/49) | 1092, 1111 |
| Tutte le starbase | `getAllStarbasesForFaction` | 7796 |
| Velocità, tempi | `calculateWarpTime`, `calculateSubwarpTime`, `warpSpeed` | 999, 1080 |

Note:
- Bastano `playerProfileId` e un RPC di lettura: nessuna firma, nessun wallet.
- Dei tipi `MoveWarp`/`MoveSubwarp` i nomi `fromSector`/`toSector` sono da confermare decodificando l'IDL; `toSector` e `warpFinish`/`arrivalTime` sono usati nel codice. Il tempo di partenza va verificato (altrimenti si ricava da distanza e velocità).
- `getProgramAccounts` con memcmp: servono RPC che lo permettano (alcuni lo limitano).
- Polling consigliato: lista flotte ogni ~60 s, `getMultipleAccounts` sulle sole flotte note ogni ~10-15 s.

## Da definire
- RPC: la chiave Ironforge di sly è bloccata fuori dal browser di Star Atlas; il server usa l'RPC pubblico Solana (funziona, in sola lettura). Se arrivano limiti di rate, passare a un RPC proprio in `server/config.js`.
- Posizione per `MineAsteroid` e `StarbaseLoadingBay`: i dati non contengono il settore; va ricavato da `planet`/`starbase` (account collegati).
- Gestione del processo: pm2 (decisa; file `ecosystem.config.js`, avvio al boot con `pm2 startup`).
- Porta di ascolto: 3000 (decisa).

## Prossimo passo
Fase 0 + 1: trovare in sly.js le funzioni di lettura flotte e produrre il primo JSON di flotte reali.
