"""Build a deterministic ChatGPT-uploadable ZIP for the portable OMEGA skill.

This packages instructions and Markdown references only. It does not install the
OMEGA runtime, register tools, or claim native ChatGPT execution support.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "exports" / "chatgpt" / "omega" / "SKILL.md"
REFERENCES = ROOT / ".claude" / "skills" / "omega" / "references"
MAX_FILES = 64
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024


def checked_read(path, root):
    """Read a regular file below root, rejecting symlinks and oversized content."""
    root = root.resolve(strict=True)
    current = root
    relative = path.relative_to(root)
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink is not allowed in skill bundle: {relative}")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"Source escapes root or is not a file: {relative}")
    data = resolved.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"Source exceeds per-file limit: {relative}")
    return data


def validate_skill(markdown):
    text = markdown.decode("utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md front matter is not closed")
    front = text[4:end]
    fields = {}
    for line in front.splitlines():
        match = re.fullmatch(r"([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*?)\s*", line)
        if not match:
            raise ValueError("Only simple one-line YAML metadata is supported")
        key, value = match.groups()
        if key in fields or not value:
            raise ValueError("Metadata keys must be unique and non-empty")
        fields[key] = value.strip('"').strip("'")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields.get("name", "")):
        raise ValueError("Skill name must be lowercase kebab-case")
    description = fields.get("description", "")
    if not description or len(description) > 1024:
        raise ValueError("Skill description must be 1-1024 characters")
    if "disable-model-invocation" in fields or "argument-hint" in fields:
        raise ValueError("Claude-specific metadata must not be included")
    return text, fields


def collect_files():
    entry_data = checked_read(ENTRY, ROOT)
    text, fields = validate_skill(entry_data)
    files = {"SKILL.md": entry_data}
    for path in sorted(REFERENCES.glob("*.md")):
        if path.is_symlink():
            raise ValueError(f"Symlink reference is not allowed: {path.name}")
        data = checked_read(path, ROOT)
        files[f"references/{path.name}"] = data
    if not files or len(files) > MAX_FILES:
        raise ValueError("Skill file-count limit exceeded")
    total = sum(len(data) for data in files.values())
    if total > MAX_TOTAL_BYTES:
        raise ValueError("Skill uncompressed byte limit exceeded")
    for relative in re.findall(r"`(references/[A-Za-z0-9_.-]+\.md)`", text):
        if relative not in files:
            raise ValueError(f"Referenced file is missing: {relative}")
    return files, fields


def build(output, force=False):
    output = Path(output)
    if not output.is_absolute():
        output = ROOT / output
    output = Path(os.path.abspath(output))
    if not output.is_relative_to(ROOT):
        raise ValueError("Output must stay inside this repository")
    parent = output.parent
    if output.is_symlink() or any(p.is_symlink() for p in [parent, *parent.parents] if p != ROOT.parent):
        raise ValueError("Output path must not traverse symlinks")
    parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not force:
        raise ValueError("Output already exists; pass --force to replace this generated artifact")
    files, fields = collect_files()
    manifest = []
    mode = "w" if force else "x"
    with zipfile.ZipFile(output, mode=mode, compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
            manifest.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise ValueError("Exported ZIP contains unsafe or duplicate paths")
        if "SKILL.md" not in names:
            raise ValueError("Exported ZIP has no root SKILL.md")
        validate_skill(archive.read("SKILL.md"))
        for item in manifest:
            if hashlib.sha256(archive.read(item["path"])).hexdigest() != item["sha256"]:
                raise ValueError("ZIP content hash mismatch")
    return {"passed": True, "archive": str(output.relative_to(ROOT)), "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "skill": fields["name"], "files": manifest, "file_count": len(files), "uncompressed_bytes": sum(x["bytes"] for x in manifest),
            "runtime_included": False, "native_chatgpt_execution_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".omega/chatgpt-export/omega-chatgpt.zip")
    parser.add_argument("--force", action="store_true", help="replace the generated output archive")
    args = parser.parse_args()
    try:
        report = build(args.output, args.force)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
