const path = require('path');
const { Connection, PublicKey, Keypair } = require('@solana/web3.js');
const anchor = require('@coral-xyz/anchor');
const config = require('./config');
const sageIDL = require('./idl/sage.json');

const entries = require(config.rpcPoolFile)
  .filter(e => e.url && (e.plrProfile_success > 0 || e.plrProfile_total === 0))
  .filter((e, i, a) => a.findIndex(x => x.url === e.url) === i)
  .map(e => {
    const connection = new Connection(e.url, { commitment: 'confirmed', fetch: require('node-fetch') });
    const provider = new anchor.AnchorProvider(connection, new anchor.Wallet(Keypair.generate()), {});
    return {
      name: e.name,
      rate: e.plrProfile_total ? e.plrProfile_success / e.plrProfile_total : 0.5,
      cooldownMs: e.cooldownMs || 60000,
      downUntil: 0,
      connection,
      sage: new anchor.Program(sageIDL, new PublicKey(config.sageProgramId), provider),
    };
  })
  .sort((a, b) => b.rate - a.rate);

// Prova gli endpoint in ordine di affidabilità; quelli in errore vanno in cooldown.
async function withRpc(fn) {
  const now = Date.now();
  const candidates = entries.filter(e => e.downUntil <= now);
  let lastErr = new Error('nessun RPC disponibile');
  for (const e of candidates.length ? candidates : entries) {
    try {
      return await fn(e);
    } catch (err) {
      e.downUntil = Date.now() + e.cooldownMs;
      lastErr = err;
      console.error(`[pool] ${e.name} fallito: ${String(err.message).slice(0, 100)}`);
    }
  }
  throw lastErr;
}

module.exports = { withRpc, sageCoder: entries[0].sage.coder };
