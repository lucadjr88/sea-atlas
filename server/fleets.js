require('./polyfill');
const { PublicKey } = require('@solana/web3.js');
const { withRpc, sageCoder } = require('./pool');
const config = require('./config');

const STATES = ['StarbaseLoadingBay', 'Idle', 'MineAsteroid', 'MoveWarp', 'MoveSubwarp', 'Respawn', 'StarbaseUpgrade', 'ReadyToExitWarp'];
const STATE_OFFSET = 439;

const sector = s => [s[0].toNumber(), s[1].toNumber()];

// Stesso layout di getFleetState() in sly.js: byte di stato + dati a offset 439.
function decodeState(data) {
  const rest = data.subarray(STATE_OFFSET);
  const state = STATES[rest[0]] || 'Unknown';
  const body = rest.subarray(1);
  const out = { state };
  if (state === 'Idle') out.sector = sector(sageCoder.types.decode('Idle', body).sector);
  if (state === 'MoveWarp') {
    const m = sageCoder.types.decode('MoveWarp', body);
    Object.assign(out, { from: sector(m.fromSector), to: sector(m.toSector), departure: m.warpStart.toNumber() * 1000, arrival: m.warpFinish.toNumber() * 1000 });
  }
  if (state === 'MoveSubwarp') {
    const m = sageCoder.types.decode('MoveSubwarp', body);
    Object.assign(out, { from: sector(m.fromSector), to: sector(m.toSector), departure: m.departureTime.toNumber() * 1000, arrival: m.arrivalTime.toNumber() * 1000 });
  }
  // Questi stati non contengono il settore: puntano all'account (pianeta o starbase) che lo contiene.
  if (state === 'MineAsteroid') out.ref = { type: 'planet', key: sageCoder.types.decode('MineAsteroid', body).asteroid.toString() };
  if (state === 'StarbaseLoadingBay') out.ref = { type: 'starbase', key: sageCoder.types.decode('StarbaseLoadingBay', body).starbase.toString() };
  return out;
}

const refSectors = new Map();

async function resolveRefs(list, connection) {
  const missing = [...new Map(list.filter(f => f.ref && !refSectors.has(f.ref.key)).map(f => [f.ref.key, f.ref])).values()];
  if (missing.length) {
    const infos = await connection.getMultipleAccountsInfo(missing.map(r => new PublicKey(r.key)));
    missing.forEach((r, i) => {
      if (!infos[i]) return;
      const decoded = sageCoder.accounts.decode(r.type, infos[i].data);
      refSectors.set(r.key, sector(decoded.sector));
    });
  }
  for (const f of list) {
    if (!f.ref) continue;
    const s = refSectors.get(f.ref.key);
    if (s) f.sector = s;
    delete f.ref;
  }
}

const SIZE_CLASSES = ['xxSmall', 'xSmall', 'small', 'medium', 'large', 'capital', 'commander', 'titan'];

// Classe più grande presente nella flotta.
function largestSize(shipCounts) {
  return [...SIZE_CLASSES].reverse().find(k => shipCounts[k] > 0) ?? 'small';
}

const label = bytes => Buffer.from(bytes).toString('utf8').replace(/\0/g, '');

async function fetchFleets() {
  const profile = config.playerProfileId;
  return withRpc(async ({ sage, connection }) => {
    const [owned, borrowed] = await Promise.all([
      sage.account.fleet.all([{ memcmp: { offset: 41, bytes: profile } }]),
      sage.account.fleet.all([{ memcmp: { offset: 105, bytes: profile } }]),
    ]);
    const fleets = [...owned, ...borrowed];
    const infos = await connection.getMultipleAccountsInfo(fleets.map(f => f.publicKey));
    const list = fleets.map((f, i) => ({
      id: f.publicKey.toString(),
      name: label(f.account.fleetLabel),
      borrowed: i >= owned.length,
      size: largestSize(f.account.shipCounts),
      ships: f.account.shipCounts.total,
      // Fine del cooldown di scansione (ms): finché è attivo la flotta sta facendo scanning SDU.
      scanCooldownEnd: f.account.scanCooldownExpiresAt.toNumber() * 1000,
      ...decodeState(infos[i].data),
    }));
    await resolveRefs(list, connection);
    return list;
  });
}

module.exports = { fetchFleets };

if (require.main === module) {
  fetchFleets().then(f => console.log(JSON.stringify(f, null, 2))).catch(e => { console.error(e); process.exit(1); });
}
