"""index_corpus.py — index our local dev blueprints/skills/strategies (*.md).

Walks C:\ae\hermes-fork, excludes vendored website/ and contest-submission/
duplicates, captures path + size + first-heading title, and writes SYNC_INDEX.json.
Also scans C:\ae outside the fork (templates, daollc, site) into SYNC_INDEX_EXT.json.

Run:  python index_corpus.py
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone

FORK = r"C:\ae\hermes-fork"
EXT = r"C:\ae"
EXCLUDE = ["/website/", "/contest-submission/"]
SKIP = ("node_modules", ".git", ".pytest_cache", ".vscode", "__pycache__", ".venv", "venv")


def title_of(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("#"):
                    return line.lstrip("#").strip()
                if line and not line.startswith(("<", "|", "!", "```")):
                    return line[:80]
    except Exception:
        pass
    return "(untitled)"


def categorize(rel: str) -> str:
    r = "/" + rel  # normalize for prefix checks
    if "/blueprints/" in r:
        return "blueprint"
    if "/skills/" in r or rel.startswith("skills/"):
        return "skill"
    if "/docs/" in r or rel.startswith("docs/"):
        return "doc"
    if "/llm-bench-rig/" in r or "/optional-skills/" in r:
        return "skill"
    if rel.lower().startswith("readme"):
        return "readme"
    if rel in ("OPENSOURCEWARE_250.md", "CAPABILITIES.md", "SPEC.md",
               "PR_BODY.md", "PR_DESCRIPTION.md", "AGENTS.md"):
        return "manifest"
    if rel.startswith(".plans/"):
        return "doc"
    return "other"


def walk(root: str, exclude_vendored: bool) -> list[dict]:
    out = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fn in files:
            if not fn.lower().endswith(".md"):
                continue
            full = os.path.join(r, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if exclude_vendored and any(ex in "/" + rel for ex in EXCLUDE):
                continue
            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0
            entry = {"path": rel, "size": size, "title": title_of(full)}
            entry["cat"] = categorize(rel)
            out.append(entry)
    return out


def main() -> int:
    FORK = os.getcwd()  # C:\æ\hermes-fork (real glyph from cwd)
    EXT = os.path.dirname(FORK)  # C:\æ
    entries = walk(FORK, True)
    by_cat = {}
    for e in entries:
        by_cat.setdefault(e["cat"], []).append(e["path"])

    index = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "source": r"C:\æ\hermes-fork (excl. website/contest vendored)",
        "counts": {c: len(v) for c, v in sorted(by_cat.items(), key=lambda x: -len(x[1]))},
        "total": len(entries),
        "entries": entries,
    }
    with open("SYNC_INDEX.json", "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1, ensure_ascii=False)

    # C:\ae outside fork
    ext = []
    for r, dirs, files in os.walk(EXT):
        dirs[:] = [d for d in dirs if d not in SKIP and d != os.path.basename(FORK)]
        for fn in files:
            if fn.lower().endswith(".md"):
                full = os.path.join(r, fn)
                rel = os.path.relpath(full, EXT).replace("\\", "/")
                ext.append({"path": rel, "size": os.path.getsize(full) if os.path.exists(full) else 0})
    with open("SYNC_INDEX_EXT.json", "w", encoding="utf-8") as fh:
        json.dump({"total": len(ext), "entries": ext}, fh, indent=1, ensure_ascii=False)

    print("FORK indexed:", len(entries))
    for c, n in index["counts"].items():
        print(f"  {c:10} {n}")
    print("EXT (C:\\ae outside fork):", len(ext))
    print("wrote SYNC_INDEX.json + SYNC_INDEX_EXT.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
