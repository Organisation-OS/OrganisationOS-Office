// OrganisationOS addition; SPDX-License-Identifier: AGPL-3.0-only
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const helper = require(path.resolve(process.argv[2] || 'server/Common/sources/oosSnapshotIdentity.js'));
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'oos-snapshot-'));
let checks = 0;
function check(actual, expected) { assert.deepEqual(actual, expected); checks++; }
const base = 'a'.repeat(64), source = 'b'.repeat(64);
function proof(src = source, ordinary = true, index = 0) {
  const snapshot = helper.create(base, src);
  snapshot.append(index, Buffer.from('synthetic-change'));
  return snapshot.finish(ordinary);
}
try {
  const first = proof();
  check(first.schema, 'organisationos-converted-changes-v2');
  check(first.sourceSha256, source);
  check(first.baseSha256, base);
  check(first.reliable, true);
  check(first.changeCount, 1);
  check(first.changesSha256, proof().changesSha256);
  check(first.changesSha256 === proof('c'.repeat(64)).changesSha256, false);
  check(proof(null).reliable, false);
  check(proof(source, false).reliable, false);
  check(proof(source, true, 1).reliable, false);
  const empty = helper.create(base, source).finish(true);
  check(empty.changeCount, 0);
  check(empty.reliable, true);
  const file = path.join(root, 'source.json');
  check(helper.readSource(file), null);
  fs.writeFileSync(file, JSON.stringify({schema: 'organisationos-source-v1', sourceSha256: source}));
  check(helper.readSource(file), source);
  fs.symlinkSync(file, path.join(root, 'link'));
  check(helper.readSource(path.join(root, 'link')), null);
  fs.writeFileSync(file, '{bad');
  check(helper.readSource(file), null);
  fs.writeFileSync(file, JSON.stringify({schema: 'wrong', sourceSha256: source}));
  check(helper.readSource(file), null);
  fs.writeFileSync(file, JSON.stringify({schema: 'organisationos-source-v1', sourceSha256: 'invalid'}));
  check(helper.readSource(file), null);
  fs.writeFileSync(file, ' '.repeat(257));
  check(helper.readSource(file), null);
  const finished = helper.create(base, source);
  finished.finish(true);
  assert.throws(() => finished.finish(true)); checks++;
  assert.throws(() => finished.append(0, 'change')); checks++;
  console.log(JSON.stringify({status: 'PASS', checks, scope: 'source identity and change-sequence helper; real conversion reception separate'}));
} finally { fs.rmSync(root, {recursive: true, force: true}); }
