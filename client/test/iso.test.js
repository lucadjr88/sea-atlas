import test from 'node:test';
import assert from 'node:assert/strict';
import { movesLeft, sectorToScreen, screenToSector, setRotation } from '../src/map/iso.js';

test('verso sinistra/destra sullo schermo', () => {
  assert.equal(movesLeft(-1, 0), true);
  assert.equal(movesLeft(0, -1), true);
  assert.equal(movesLeft(1, 0), false);
  assert.equal(movesLeft(0, 1), false);
});

test('origine e verso est/nord', () => {
  assert.deepEqual(sectorToScreen(0, 0), { x: 0, y: 0 });
  assert.ok(sectorToScreen(1, 0).x > 0);
  assert.ok(sectorToScreen(0, 1).y < 0);
});

test('rotazione: screenToSector è l\'inverso di sectorToScreen', () => {
  for (let q = 0; q < 4; q++) {
    setRotation(q);
    const s = sectorToScreen(7, -13);
    const back = screenToSector(s.x, s.y);
    assert.ok(Math.abs(back.x - 7) < 1e-9 && Math.abs(back.y + 13) < 1e-9, `q=${q}`);
  }
  setRotation(0);
});

test('rotazione: quattro quarti riportano alla posizione iniziale', () => {
  const p0 = sectorToScreen(3, 5);
  setRotation(4);
  assert.deepEqual(sectorToScreen(3, 5), p0);
});
