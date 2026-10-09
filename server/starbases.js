require('./polyfill');
const fs = require('fs');
const path = require('path');
const { withRpc } = require('./pool');

const CACHE_FILE = path.join(__dirname, 'data', 'starbases.json');
const MAX_AGE_MS = 24 * 3600 * 1000;
const FACTIONS = ['Unaligned', 'MUD', 'ONI', 'Ustur'];

const label = bytes => Buffer.from(bytes).toString('utf8').replace(/\0/g, '').trim();

// Come in sly.js: il nome del sistema è il prefisso (es. "MRZ-9") del primo pianeta del settore.
async function fetchSystemNames() {
  const planets = await withRpc(({ sage }) => sage.account.planet.all());
  const bySector = new Map();
  for (const p of planets) {
    const key = `${p.account.sector[0].toNumber()},${p.account.sector[1].toNumber()}`;
    if (bySector.has(key)) continue;
    const [a, b] = label(p.account.name).split('-');
    bySector.set(key, b === undefined ? a : `${a}-${b}`);
  }
  return bySector;
}

async function fetchStarbases() {
  const [all, systems] = await Promise.all([withRpc(({ sage }) => sage.account.starbase.all()), fetchSystemNames()]);
  return all
    .map(s => ({
      id: s.publicKey.toString(),
      name: label(s.account.name),
      sector: [s.account.sector[0].toNumber(), s.account.sector[1].toNumber()],
      faction: FACTIONS[s.account.faction] ?? 'Unknown',
      level: s.account.level,
      system: systems.get(`${s.account.sector[0].toNumber()},${s.account.sector[1].toNumber()}`) ?? null,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

// Le starbase cambiano di rado: cache su disco, aggiornata al massimo una volta al giorno.
async function loadStarbases() {
  try {
    const stat = fs.statSync(CACHE_FILE);
    if (Date.now() - stat.mtimeMs < MAX_AGE_MS) return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
  } catch {}
  try {
    const list = await fetchStarbases();
    fs.mkdirSync(path.dirname(CACHE_FILE), { recursive: true });
    fs.writeFileSync(CACHE_FILE, JSON.stringify(list));
    return list;
  } catch (err) {
    console.error('[starbases]', err.message);
    return fs.existsSync(CACHE_FILE) ? JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8')) : [];
  }
}

const NAMES_FILE = path.join(__dirname, 'data', 'starbase-names.json');

// Nome mostrato: override da data/starbase-names.json ({"x,y": "nome"}), altrimenti abbreviazione del nome on-chain.
function withDisplayNames(list) {
  let overrides = {};
  try { overrides = JSON.parse(fs.readFileSync(NAMES_FILE, 'utf8')); } catch {}
  return list.map(s => ({
    ...s,
    name: overrides[`${s.sector[0]},${s.sector[1]}`]
      ?? (s.level >= 6 ? `${(s.system ?? s.faction).split('-')[0]} CSS` : null)
      ?? s.system
      ?? `${s.faction} (${s.sector[0]},${s.sector[1]})`,
  }));
}

module.exports = { loadStarbases, withDisplayNames };

if (require.main === module) {
  loadStarbases().then(l => { console.log(l.length, 'starbase'); console.table(l.map(({ name, sector, faction, level }) => ({ name, x: sector[0], y: sector[1], faction, level }))); });
}
