# Use OMEGA as a ChatGPT skill

This repository remains a Claude Code plugin by default. It now also has a separate, portable ChatGPT skill bundle. The exported bundle contains instructions and Markdown references; it does **not** install the OMEGA Python engine, Claude hooks, MCP servers, or repository permissions.

## Build the upload ZIP

From a clean checkout of this repository:

```bash
python3 tools/export_chatgpt_skill.py
```

The exporter writes:

```text
.omega/chatgpt-export/omega-chatgpt.zip
```

To replace an archive generated earlier, use `--force`. To choose another output path, use `--output PATH` (the path must remain inside the repository). The exporter uses Python standard library only and rejects symlinked sources, missing references, unsupported metadata, oversized bundles, unsafe ZIP paths and hash mismatches. It does not install packages or change global ChatGPT settings.

Review the generated JSON report and ZIP contents before uploading. The report's `native_chatgpt_execution_verified=false` is intentional: packaging success is not proof that ChatGPT selected or executed the skill.

## Upload it in ChatGPT

1. Use a ChatGPT account/workspace where Skills are available and skill uploads are enabled. Availability depends on plan and workspace policy.
2. In the ChatGPT desktop app, open **Skills** (or **Plugins → Skills**, depending on the interface).
3. Choose **Create → Upload from computer** and select `omega-chatgpt.zip`.
4. Review the skill and any safety scan or review prompt, then install/enable it.
5. Start a task that matches OMEGA's description, or explicitly invoke `@omega` if the interface offers skill mentions. Check the result and verify the skill is enabled before relying on it.

If the Skills page or upload option is unavailable, the account/workspace may not support this surface or an administrator may have disabled uploads. Do not assume the ZIP can be installed into an ordinary ChatGPT Free/Plus chat.

## What transfers and what does not

Included:
- ChatGPT-compatible `SKILL.md` metadata with `name` and `description`.
- OMEGA's 13 Markdown references, loaded progressively when relevant.
- Instructions to distinguish observed evidence, unrun checks, blockers and unknowns.

Not included:
- Claude plugin manifests, slash-command runtime, agents, hooks or MCP registration.
- An automatically running Python engine or terminal.
- GitHub authorization, filesystem access, deployment rights, or a background service.

The skill must only report commands/tests as run when the current ChatGPT session actually has a suitable tool and an observed result. Otherwise it should provide manual guidance and state the limitation.

## Validate the bundle

The repository CI runs a packaging contract check:

```bash
python3 benchmarks/chatgpt_skill_export.py
```

This checks the generated ZIP, metadata, references, paths and content hashes. It does not measure model reasoning quality, activation rate or token savings.

Official guidance:
- [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
