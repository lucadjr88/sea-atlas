import test from 'node:test';
import assert from 'node:assert/strict';
import { miningOrbit, mooringOffset } from '../src/entities/miningOrbit.js';

test('la flotta mineraria si sposta e poi pesca per il resto del ciclo di 5 secondi', () => {
  const start = miningOrbit(0);
  const middle = miningOrbit(450);
  const fishing = miningOrbit(900);
  const beforeNextMove = miningOrbit(4999);
  const nextMove = miningOrbit(5000);

  assert.equal(start.moving, true);
  assert.equal(middle.moving, true);
  assert.ok(middle.angle > start.angle && middle.angle < fishing.angle);
  assert.equal(fishing.moving, false);
  assert.equal(beforeNextMove.angle, fishing.angle);
  assert.equal(nextMove.moving, true);
  assert.equal(nextMove.angle, fishing.angle);
});

test('l\'offset separa le navi senza alterare il ciclo', () => {
  const offset = Math.PI / 2;
  const base = miningOrbit(1000);
  const shifted = miningOrbit(1000, offset);

  assert.equal(shifted.moving, base.moving);
  assert.ok(Math.abs(shifted.angle - base.angle - offset) < 1e-9);
});

test('gli slot di ormeggio restano sopra l\'isola alla distanza richiesta', () => {
  const radius = 100;
  const left = mooringOffset(radius, 0);
  const right = mooringOffset(radius, 7);

  assert.ok(left.x < 0 && left.y < 0);
  assert.ok(right.x > 0 && right.y < 0);
  for (let slot = 0; slot < 8; slot++) {
    const offset = mooringOffset(radius, slot);
    assert.ok(offset.y < 0);
    assert.ok(Math.abs(Math.hypot(offset.x, offset.y) - radius) < 1e-9);
  }
});