// Real Worker + isolated ephemeral D1, never the production member database.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE || 'C:/Users/zjh/Desktop/data/tools/wrangler/node_modules/miniflare');
const script = await readFile(new URL('../cloudflare-pages-proxy/dist/_worker.js', import.meta.url), 'utf8');
const mf = new Miniflare({modules:true, script, compatibilityDate:'2026-04-08',
  d1Databases:{MEMBER_DB:'native-excel-isolated-tests'}, bindings:{MEMBER_STORE_API_SECRET:'test-secret'}});
const origin = 'https://fruition-component.pages.dev';
const owner = 'a'.repeat(64), otherOwner = 'b'.repeat(64);
const raw = Buffer.concat([Buffer.from('PK\x03\x04SYNTHETIC-NATIVE-EXCEL-PRIVATE-'), Buffer.alloc(600000, 91)]);
const manage = (method, body, secret='test-secret') => mf.dispatchFetch(origin+'/api/bom-excel', {
  method, headers:{Authorization:'Bearer '+secret, 'Content-Type':'application/json'}, body:JSON.stringify(body)});
const issue = (id=owner, data=raw) => manage('POST', {owner:id, filename:'BOM_匹配后.xlsx', dataBase64:data.toString('base64')});
try {
  assert.equal((await issue()).status,201);
  let res = await issue(); const ticket = await res.json();
  assert.match(ticket.url, /^https:\/\/fruition-component.pages.dev\/x\/[A-Za-z0-9_-]{43}\/BOM.xlsx$/);
  assert.ok(ticket.expiresAt > Date.now()/1000 && ticket.expiresAt <= Date.now()/1000+301);
  res = await mf.dispatchFetch(ticket.url);
  assert.equal(res.status,200); assert.deepEqual(Buffer.from(await res.arrayBuffer()),raw);
  assert.match(res.headers.get('cache-control'),/no-store/);
  assert.equal(res.headers.get('referrer-policy'),'no-referrer');
  assert.match(res.headers.get('content-disposition'),/inline;.*filename\*=UTF-8/);
  assert.equal((await mf.dispatchFetch(ticket.url, {method:'HEAD'})).headers.get('content-length'),String(raw.length));
  assert.equal((await mf.dispatchFetch(ticket.url, {method:'HEAD'})).body,null);
  res = await mf.dispatchFetch(ticket.url,{headers:{Range:'bytes=100-399'}});
  assert.equal(res.status,206); assert.deepEqual(Buffer.from(await res.arrayBuffer()),raw.subarray(100,400));
  res = await mf.dispatchFetch(ticket.url,{headers:{Range:'bytes=-20'}});
  assert.deepEqual(Buffer.from(await res.arrayBuffer()),raw.subarray(-20));
  for (const range of ['bytes=9999999-','bytes=3-1','bytes=0-2,4-6','bytes=-']) {
    assert.equal((await mf.dispatchFetch(ticket.url,{headers:{Range:range}})).status,416);
  }
  assert.equal((await mf.dispatchFetch(ticket.url,{method:'PUT',body:'replace'})).status,405);
  assert.equal((await mf.dispatchFetch(ticket.url,{method:'OPTIONS'})).status,204);
  assert.equal((await manage('DELETE',{owner},'wrong-secret')).status,403);
  assert.equal((await mf.dispatchFetch(ticket.url.replace(/\/x\/./,'/x/Z'))).status,404);
  const db = await mf.getD1Database('MEMBER_DB');
  const stored = await db.prepare('SELECT token_hash, data FROM bom_excel_chunks').all();
  assert.ok(stored.results.length > 1, 'large workbook is chunked below D1 row limits');
  const ciphertext = Buffer.concat(stored.results.map(row=>Buffer.from(row.data)));
  assert.ok(!ciphertext.includes(Buffer.from('SYNTHETIC-NATIVE-EXCEL-PRIVATE')));
  assert.notDeepEqual(ciphertext.subarray(0,raw.length),raw);
  assert.ok(!JSON.stringify(stored).includes(ticket.url.split('/')[4]));
  await manage('DELETE',{owner:otherOwner});
  assert.equal((await mf.dispatchFetch(ticket.url)).status,200);
  const damaged = Uint8Array.from(stored.results[0].data); damaged[0] ^= 1;
  await db.prepare('UPDATE bom_excel_chunks SET data = ? WHERE token_hash = ? AND part = 0')
    .bind(damaged.buffer,stored.results[0].token_hash).run();
  assert.equal((await mf.dispatchFetch(ticket.url)).status,503,'tampered ciphertext must not be returned');
  const replacement = await (await issue()).json();
  assert.equal((await mf.dispatchFetch(ticket.url)).status,404);
  await manage('DELETE',{owner});
  assert.equal((await mf.dispatchFetch(replacement.url)).status,404);
  assert.equal((await db.prepare('SELECT COUNT(*) n FROM bom_excel_chunks').first()).n,0);
  const expiring = await (await issue()).json();
  await db.prepare('UPDATE bom_excel_tickets SET expires_at = 1').run();
  assert.equal((await mf.dispatchFetch(expiring.url)).status,404);
  assert.equal((await db.prepare('SELECT COUNT(*) n FROM bom_excel_chunks').first()).n,0);
  assert.equal((await issue(owner,Buffer.from('not-an-xlsx'))).status,400);
  assert.equal((await manage('POST',{owner:'../../unsafe'})).status,400);
  assert.equal((await issue(owner,Buffer.alloc(8*1024*1024+1))).status,413);
  assert.equal((await mf.dispatchFetch(origin+'/api/bom-excel',{method:'GET'})).status,403);
  await db.prepare(`INSERT INTO bom_excel_tickets VALUES ('quota', ?, ?, 67108864, 'q', 'q')`).bind(otherOwner,Math.floor(Date.now()/1000)+300).run();
  assert.equal((await issue()).status,503);
  console.log('PASS: native Excel Worker/D1 auth, encryption, full/chunked bytes, range, HEAD, expiry, removal, replacement, isolation and quota.');
} finally { await mf.dispose(); }
