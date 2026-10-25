# RTK integration: reduce noise without losing evidence

RTK is an optional host-level CLI wrapper for reducing repetitive terminal output. It is not required by OMEGA/HUTAO, and it does not replace the Python engine's compact JSON, explicit source packets, evidence references, or quality gates.

## Safety contract

- Do not install RTK automatically from the plugin, run lifecycle scripts, or edit the user's shell configuration without their explicit action.
- Treat RTK output reduction as a presentation optimization, not proof that model token billing decreased.
- Preserve exit codes, stderr, failing test names, assertion diffs, compiler diagnostics, security findings, and relevant command arguments.
- If a summarized result is ambiguous, incomplete, truncated, or inconsistent with the exit code, rerun the underlying command directly and inspect the raw output.
- Never skip a gate, weaken an assertion, reuse stale pass/fail results, or shorten acceptance criteria to save context.
- Use OMEGA's existing `--compact`, `context --select`, and `gates --summary --compact` independently of RTK. These options are opt-in and preserve source payloads / gate outcomes according to the contracts in [TOKEN_EFFICIENCY.md](TOKEN_EFFICIENCY.md).

## Opt-in setup

Install RTK only from its official repository after reviewing the release and installation instructions:

- https://github.com/rtk-ai/rtk

If you choose to initialize its shell integration, first inspect the instructions for your shell and back up the relevant config. RTK documents `rtk init -g`; this is a user-level shell configuration change, so do not run it implicitly as part of plugin installation.

Verify the command is available:

```bash
rtk --version
```

Run the same representative task with RTK disabled and enabled. Compare command exit status, test counts, failure names, stderr, and diagnostic detail. When the wrapper obscures evidence, use the underlying command directly.

## Evaluation protocol

Use a fixed task corpus and the same repository revision, model, prompt, acceptance criteria, and test gates for both runs. Record:

1. Input/output/cache token counts from the provider/runtime when available.
2. Task completion and all acceptance checks.
3. Test totals and exact failure diagnostics.
4. Raw versus summarized command output bytes.
5. Whether a human or grader found any missing evidence.

A decrease in terminal bytes is not the same as a decrease in provider-billed tokens. Do not claim a quality-preserving token reduction until the native A/B evaluation has completed. OMEGA's existing byte-equivalence benchmark covers its own deterministic formatting transformations; it does not establish RTK's behavior or native Claude answer quality.

## Rollback

Disable or remove the RTK shell integration using the official instructions for the shell and version installed. Restore the backed-up shell configuration if needed. OMEGA continues to work without RTK; no project dependency or plugin manifest change is required to disable it.
