import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, lstat, writeFile, readFile, symlink } from 'node:fs/promises';
import { join } from 'node:path';
import { execFileSync, spawn } from 'node:child_process';
import { PassThrough, Readable } from 'node:stream';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { buildArguments, runReadOnly, readRequest } from './omega-bridge.ts';

const root = fileURLToPath(new URL('../../', import.meta.url));
await mkdir(join(root, '.omega'), { recursive: true });
if ((await lstat(join(root, '.omega'))).isSymbolicLink()) throw new Error('Symlink runtime test directory refused');
test('real Python map returns bounded repository metadata', async () => {
  const response = await runReadOnly({ command: 'map' }, root);
  assert.equal(response.exitCode, 0); assert.ok(response.result.files.some(row => row.path === 'omega_cli.py'));
});
test('real Python plan retains workflow and agent limits', async () => {
  const response = await runReadOnly({ command: 'plan', complexity: 'high', conflict: true }, root);
  assert.equal(response.exitCode, 0); assert.equal(response.result.isolation, 'worktree'); assert.equal(response.result.max_concurrent_agents, 2);
});
test('mutations, shell commands and unknown fields never reach engine', () => {
  for (const request of [{ command: 'gates' }, { command: 'isolate' }, { command: 'git push' }, { command: 'map', argv: ['--project-root','/tmp'] }]) {
    assert.throws(() => buildArguments(request, root));
  }
});
test('paths cannot escape configured root or smuggle an executable option', () => {
  for (const path of ['../outside','/etc/passwd','\0','']) assert.throws(() => buildArguments({ command: 'context', selections: [path] }, root));
  assert.throws(() => buildArguments({ command: 'map' }, '.'));
  assert.throws(() => buildArguments({ command: 'map', complexity: 'low' }, root));
});
test('context content equals direct Python output, without JS rewriting', async () => {
  const request = { command: 'context', selections: ['omega_cli.py:1:6'] };
  const bridged = await runReadOnly(request, root);
  const direct = JSON.parse(execFileSync('python3', buildArguments(request, root), { encoding: 'utf8' }));
  assert.deepEqual(bridged.result, direct);
});
test('output and timeout bounds reject instead of returning partial success', async () => {
  await assert.rejects(runReadOnly({ command: 'map' }, root, { maxOutputBytes: 32 }), /budget/);
  await assert.rejects(runReadOnly({ command: 'map' }, root, { timeoutMs: 1 }), /timeout/);
  await assert.rejects(runReadOnly({ command: 'map' }, root, { timeoutMs: -1 }), /bounds/);
});
test('unavailable Python executable fails explicitly', async () => {
  await assert.rejects(runReadOnly({ command: 'map' }, root, { python: '/missing/omega-python' }), /Unable to launch/);
});
test('Python semantic failure is retained rather than converted to success', async () => {
  const folder = await mkdtemp(join(root, '.omega', 'ts-proposal-'));
  await writeFile(join(folder, '.gitignore'), '.omega/\n');
  await writeFile(join(folder, 'package.json'), JSON.stringify({ scripts: { test: 'node --test' } }));
  execFileSync('git', ['init','-q'], { cwd: folder });
  const response = await runReadOnly({ command: 'project-workflow-adapter' }, folder);
  assert.equal(response.exitCode, 1); assert.equal(response.result.status, 'proposal-needs-review');
  assert.equal(response.result.files_written, false);
});
test('Python source protections reject a selected symlink', async () => {
  const folder = await mkdtemp(join(root, '.omega', 'ts-symlink-'));
  await writeFile(join(folder, 'safe.py'), 'value=42\n');
  await symlink(join(folder, 'safe.py'), join(folder, 'alias.py'));
  execFileSync('git', ['init','-q'], { cwd: folder });
  const response = await runReadOnly({ command: 'context', selections: ['alias.py'] }, folder);
  assert.equal(response.exitCode, 2); assert.match(response.result.error, /Symlink/);
  assert.equal(await readFile(join(folder, 'safe.py'), 'utf8'), 'value=42\n');
});
test('open stdin without EOF is timed out and closed', async () => {
  const stream = new PassThrough();
  stream.write('{"command":"map"}');
  await assert.rejects(readRequest(stream, 20), /input timeout/);
  assert.equal(stream.destroyed, true);
});
test('stdin rejects oversized and invalid UTF-8 data', async () => {
  await assert.rejects(readRequest(Readable.from([Buffer.alloc(16385, 'x')])), /byte budget/);
  await assert.rejects(readRequest(Readable.from([Buffer.from([255])])));
});
test('aggregate request byte budget also applies to direct API calls', () => {
  assert.throws(() => buildArguments({ command: 'context', selections: ['x'.repeat(4000), 'y'.repeat(4000), 'z'.repeat(4000), 'a'.repeat(4000), 'b'.repeat(4000)] }, root), /byte budget/);
  assert.throws(() => buildArguments({ command: 'context', selections: ['á'.repeat(4000), 'á'.repeat(4000), 'á'.repeat(4000)] }, root), /byte budget/);
});
test('pre-aborted and active requests honour cancellation', async () => {
  const before = new AbortController(); before.abort();
  await assert.rejects(runReadOnly({ command: 'map' }, root, { signal: before.signal }), /cancelled/);
  const active = new AbortController();
  const pending = runReadOnly({ command: 'map' }, root, { signal: active.signal }); active.abort();
  await assert.rejects(pending, /cancelled/);
});
test('CLI deadline includes a caller that never ends stdin', async () => {
  const bridge = fileURLToPath(new URL('./omega-bridge.ts', import.meta.url));
  const child = spawn(process.execPath, [bridge, '--project-root', root, '--timeout-ms', '30'], { stdio: ['pipe','pipe','pipe'] });
  let stderr = ''; child.stderr.on('data', value => { stderr += value.toString(); });
  const watchdog = setTimeout(() => child.kill('SIGKILL'), 3000);
  try {
    child.stdin.write('{"command":"map"}');
    const [code] = await once(child, 'close');
    assert.equal(code, 2); assert.match(stderr, /input timeout/);
  } finally { clearTimeout(watchdog); child.stdin.destroy(); }
});
test('stdin deadline rejects invalid timeout values', async () => {
  for (const timeout of [0,-1,NaN,60001]) await assert.rejects(readRequest(Readable.from([]), timeout), /timeout/);
});
