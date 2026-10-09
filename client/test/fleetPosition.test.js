import test from 'node:test';
import assert from 'node:assert/strict';
import { fleetPosition } from '../src/model/fleetPosition.js';
import { isStarbaseSector, starbaseSectorSet } from '../src/model/starbaseSectors.js';

const moving = { state: 'MoveSubwarp', from: [0, 0], to: [10, -20], departure: 1000, arrival: 3000 };

test('flotta idle: posizione = settore', () => {
  assert.deepEqual(fleetPosition({ state: 'Idle', sector: [8, -17] }, 0), { x: 8, y: -17, heading: null, progress: null });
});

test('movimento: interpolazione lineare', () => {
  const p = fleetPosition(moving, 2000);
  assert.equal(p.x, 5);
  assert.equal(p.y, -10);
  assert.equal(p.progress, 0.5);
});

test('movimento: clamp prima della partenza e dopo l\'arrivo', () => {
  assert.equal(fleetPosition(moving, 0).x, 0);
  assert.equal(fleetPosition(moving, 9999).x, 10);
});

test('stato senza posizione -> null', () => {
  assert.equal(fleetPosition({ state: 'MineAsteroid' }, 0), null);
});

test('miniera/molo: posizione dal settore risolto dal server', () => {
  assert.equal(fleetPosition({ state: 'MineAsteroid', sector: [3, 4] }, 0).x, 3);
  assert.equal(fleetPosition({ state: 'StarbaseLoadingBay', sector: [3, 4] }, 0).y, 4);
});

test('riconosce solo i settori esatti delle starbase', () => {
  const sectors = starbaseSectorSet([{ sector: [3, 4] }, { sector: [-8, 12] }]);

  assert.equal(isStarbaseSector({ x: 3, y: 4 }, sectors), true);
  assert.equal(isStarbaseSector({ x: 3, y: 5 }, sectors), false);
  assert.equal(isStarbaseSector({ x: 3.01, y: 4 }, sectors), false);
});
