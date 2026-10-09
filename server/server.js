require('./polyfill');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');
const config = require('./config');
const { fetchFleets } = require('./fleets');
const { loadStarbases, withDisplayNames } = require('./starbases');

const POLL_MS = 30000;
const CLIENT_DIR = path.resolve(__dirname, '../client');
const ASSETS_DIR = path.resolve(__dirname, '../demo/assets');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };

let starbases = [];
let snapshot = { updatedAt: 0, error: null, fleets: [] };

const payload = () => JSON.stringify(snapshot);

async function poll() {
  try {
    snapshot = { updatedAt: Date.now(), error: null, fleets: await fetchFleets() };
  } catch (err) {
    snapshot = { ...snapshot, error: String(err.message).slice(0, 200) };
    console.error('[poll]', snapshot.error);
  }
  for (const c of wss.clients) if (c.readyState === 1) c.send(payload());
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/fleets') {
    res.writeHead(200, { 'content-type': 'application/json', 'access-control-allow-origin': '*' });
    return res.end(payload());
  }
  if (url.pathname === '/starbases') {
    res.writeHead(200, { 'content-type': 'application/json' });
    return res.end(JSON.stringify(withDisplayNames(starbases)));
  }
  const rel = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
  const [root, sub] = rel.startsWith('/assets/') ? [ASSETS_DIR, rel.slice('/assets'.length)] : [CLIENT_DIR, rel];
  const file = path.resolve(root, '.' + sub);
  if (!file.startsWith(root + path.sep)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
});

const wss = new WebSocketServer({ server, path: '/ws' });
wss.on('connection', ws => ws.send(payload()));

server.listen(config.port, () => {
  console.log(`http://localhost:${config.port}`);
  loadStarbases().then(list => { starbases = list; });
  poll();
  setInterval(poll, POLL_MS);
});
