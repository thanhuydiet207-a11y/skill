import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, lstat, writeFile, readFile, symlink } from 'node:fs/promises';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { buildArguments, runReadOnly } from './omega-bridge.ts';

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
