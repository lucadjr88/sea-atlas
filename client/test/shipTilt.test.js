import test from 'node:test';
import assert from 'node:assert/strict';
import { shipTilt } from '../src/map/shipTilt.js';

const angleDifference = (first, second) => Math.atan2(Math.sin(first - second), Math.cos(first - second));

test('la prua segue le quattro direzioni isometriche senza capovolgere lo sprite', () => {
  const axis = Math.atan2(30, 58);
  for (const direction of [
    { x: 58, y: 30 },
    { x: 58, y: -30 },
    { x: -58, y: -30 },
    { x: -58, y: 30 },
  ]) {
    const spriteAxis = direction.x < 0 ? Math.PI - axis : axis;
    const heading = Math.atan2(direction.y, direction.x);
    const rotation = shipTilt(direction);
    assert.ok(Math.abs(angleDifference(spriteAxis + rotation, heading)) < 1e-9);
    assert.ok(Math.abs(rotation) <= Math.PI / 2);
  }
});

test('la direzione verticale non rovescia lo sprite', () => {
  assert.ok(Math.abs(shipTilt({ x: 0, y: -1 })) <= Math.PI / 2);
  assert.ok(Math.abs(shipTilt({ x: 0, y: 1 })) <= Math.PI / 2);
});
