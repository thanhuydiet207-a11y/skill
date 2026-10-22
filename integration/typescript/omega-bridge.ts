/** Thin, bounded read-only facade. Python remains the policy and evidence engine. */
import { spawn } from 'node:child_process';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const engine = fileURLToPath(new URL('../../omega_cli.py', import.meta.url));
const commands = new Set(['map', 'plan', 'audit', 'context', 'memory-read',
  'skill-compatibility-audit', 'effective-policy-explainer', 'workflow-handoff-contract',
  'skill-interference-benchmark', 'project-workflow-adapter', 'evidence-reconciler',
  'memory-reconciliation', 'context-sufficiency-check']);

export type BridgeRequest = {
  command: string;
  input?: string;
  record?: string;
  selections?: string[];
  skillRoots?: string[];
  hookConfigs?: string[];
  complexity?: 'low' | 'medium' | 'high';
  conflict?: boolean;
};
export type BridgeOptions = { python?: string; timeoutMs?: number; maxOutputBytes?: number };
export type BridgeResult = { exitCode: number; result: unknown; scope: 'read-only Python facade' };

export function buildArguments(value: unknown, projectRoot: string): string[] {
  if (!isAbsolute(projectRoot)) throw new Error('An absolute trusted project root is required');
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Expected request object');
  const request = value as Record<string, unknown>;
  const known = new Set(['command', 'input', 'record', 'selections', 'skillRoots', 'hookConfigs', 'complexity', 'conflict']);
  if (Object.keys(request).some(key => !known.has(key))) throw new Error('Unknown request field');
  if (typeof request.command !== 'string' || !commands.has(request.command)) throw new Error('Command is outside read-only facade');
  const command = request.command;
  const argv = [engine, '--project-root', projectRoot, command, '--compact'];
  function string(value: unknown): string {
    if (typeof value !== 'string' || !value || value.includes('\0') || value.length > 4096) throw new Error('Invalid bounded string');
    return value;
  }
  function path(value: unknown, range = false): string {
    const text = string(value);
    const source = range ? text.replace(/:[1-9][0-9]*:[1-9][0-9]*$/, '') : text;
    const rel = relative(resolve(projectRoot), resolve(projectRoot, source));
    if (!rel || rel === '..' || rel.startsWith('..' + sep) || isAbsolute(rel)) throw new Error('Path escapes configured project');
    return text;
  }
  if (request.input !== undefined) {
    if (!['plan','context','skill-compatibility-audit','effective-policy-explainer','workflow-handoff-contract',
      'skill-interference-benchmark','memory-reconciliation','context-sufficiency-check'].includes(command)) throw new Error('Input is unsupported for command');
    argv.push('--input', path(request.input));
  }
  if (request.record !== undefined) {
    if (!['memory-read','memory-reconciliation','evidence-reconciler'].includes(command)) throw new Error('Record is unsupported for command');
    argv.push('--record', path(request.record));
  }
  for (const [key, flag, allowed] of [
    ['selections','--select',['audit','context']],
    ['skillRoots','--skill-root',['skill-compatibility-audit']],
    ['hookConfigs','--hook-config',['skill-compatibility-audit']],
  ] as const) {
    if (request[key] === undefined) continue;
    const values = request[key];
    if (!(allowed as readonly string[]).includes(command) || !Array.isArray(values) || values.length > 32) throw new Error('Invalid command list');
    for (const value of values) argv.push(flag, path(value, key === 'selections' && command === 'context'));
  }
  if (request.complexity !== undefined) {
    if (command !== 'plan' || !['low','medium','high'].includes(string(request.complexity))) throw new Error('Invalid complexity');
    argv.push('--complexity', request.complexity as string);
  }
  if (request.conflict !== undefined) {
    if (command !== 'plan' || typeof request.conflict !== 'boolean') throw new Error('Invalid conflict');
    if (request.conflict) argv.push('--conflict');
  }
  return argv;
}

export async function runReadOnly(request: unknown, projectRoot: string, options: BridgeOptions = {}): Promise<BridgeResult> {
  const argv = buildArguments(request, projectRoot);
  const timeoutMs = options.timeoutMs ?? 15000;
  const maxOutputBytes = options.maxOutputBytes ?? 131072;
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 60000 ||
      !Number.isInteger(maxOutputBytes) || maxOutputBytes < 1 || maxOutputBytes > 1048576) throw new Error('Invalid bridge bounds');
  return new Promise((accept, reject) => {
    const child = spawn(options.python ?? 'python3', argv, { shell: false, detached: true, stdio: ['ignore','pipe','pipe'] });
    const stdout: Buffer[] = []; const stderr: Buffer[] = []; let bytes = 0; let settled = false;
    function fail(message: string) {
      if (settled) return;
      settled = true; clearTimeout(timer);
      if (child.pid) { try { process.kill(-child.pid, 'SIGKILL'); } catch {} }
      reject(new Error(message));
    }
    const timer = setTimeout(() => fail('Python engine timeout; no success returned'), timeoutMs);
    for (const [stream, parts] of [[child.stdout, stdout], [child.stderr, stderr]] as const) {
      stream.on('data', (chunk: Buffer) => {
        if (settled) return;
        bytes += chunk.length;
        if (bytes > maxOutputBytes) { fail('Python output exceeds budget; no truncated success returned'); return; }
        parts.push(chunk);
      });
    }
    child.on('error', () => fail('Unable to launch trusted Python engine'));
    child.on('close', code => {
      if (settled) return;
      clearTimeout(timer); settled = true;
      try {
        if (code === null || ![0,1,2].includes(code)) throw new Error('Python process terminated without valid CLI result');
        const decoder = new TextDecoder('utf-8', { fatal: true });
        const text = decoder.decode(Buffer.concat(stdout.length ? stdout : stderr));
        const result: unknown = JSON.parse(text);
        if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('Invalid Python result envelope');
        accept({ exitCode: code, result, scope: 'read-only Python facade' });
      } catch { reject(new Error('Python output is not a valid complete JSON result')); }
    });
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 4 || process.argv[2] !== '--project-root') throw new Error('Usage: node omega-bridge.ts --project-root ABS; request JSON on stdin');
    const chunks: Buffer[] = []; let bytes = 0;
    for await (const chunk of process.stdin) {
      bytes += chunk.length;
      if (bytes > 16384) throw new Error('Request exceeds byte budget');
      chunks.push(chunk);
    }
    const result = await runReadOnly(JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks))), process.argv[3]);
    process.stdout.write(JSON.stringify(result) + '\n'); process.exitCode = result.exitCode;
  } catch (error) {
    process.stderr.write(JSON.stringify({ error: error instanceof Error ? error.message : 'Bridge error' }) + '\n'); process.exitCode = 2;
  }
}
