import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyStarbases } from '../src/model/starbaseKind.js';

const sb = (name, sector, faction, level = 5) => ({ name, sector, faction, level });

test('classificazione css / faction / mrz', () => {
  const kinds = classifyStarbases([
    sb('MUD CSS', [0, -39], 'MUD', 6),
    sb('MUD-4', [-2, -44], 'MUD'),
    sb('MUD (-10,-37)', [-10, -37], 'MUD'),
    sb('MUD (-15,-33)', [-15, -33], 'MUD'),
    sb('MRZ-6', [11, -16], 'MUD'),
  ]).map(s => s.kind);
  assert.deepEqual(kinds, ['css', 'faction', 'faction', 'mrz', 'mrz']);
});
