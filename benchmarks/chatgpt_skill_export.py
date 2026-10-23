"""Contract smoke test for the ChatGPT skill ZIP exporter; no model calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "export_chatgpt_skill.py"
spec = importlib.util.spec_from_file_location("export_chatgpt_skill", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    scratch = ROOT / ".omega"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chatgpt-skill-contract-", dir=scratch) as temp:
        output = Path(temp) / "skill.zip"
        report = module.build(output)
        if not report["passed"] or report["runtime_included"] or report["native_chatgpt_execution_verified"]:
            raise ValueError("Exporter reported unsupported runtime/native guarantees")
        with zipfile.ZipFile(output, "r") as archive:
            names = set(archive.namelist())
            if "SKILL.md" not in names or not any(name.startswith("references/") for name in names):
                raise ValueError("Bundle is missing the root skill or references")
            text, fields = module.validate_skill(archive.read("SKILL.md"))
            if fields.get("name") != "omega" or not fields.get("description"):
                raise ValueError("Skill metadata contract failed")
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                raise ValueError("Unsafe archive path found")
            missing = [line for line in text.splitlines() if "`references/" in line and not line.startswith("- ")]
            if missing:
                raise ValueError("Unexpected unresolved reference path format")
        if len(report["files"]) < 2:
            raise ValueError("Expected reference files were not packaged")
        print(json.dumps({"passed": True, "file_count": report["file_count"],
                          "archive_sha256": report["archive_sha256"],
                          "runtime_included": False,
                          "native_chatgpt_execution_verified": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
