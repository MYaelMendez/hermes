"""deploy_github_pages.py — copy deploy surfaces into the local github.io pages repo.

github.io is the POINT-OF-TRUTH surface (see TRUTH_SOURCE.md). This script
copies the canonical deploy surfaces (neuromitosis.html + aggregate.html,
baked/rolled-up by gen_neuromitosis.py / written as aggregate.html) into the
local github.io pages repo, creating it as a stub git repo if it isn't already
present.

This is the WRITE half of the loop. The inverse ingestor
(ingest_github_pages.py) reads github.io -> meta_memory; this writes our
rendered surfaces -> github.io (the truth surface). Together they keep the
cortex and the published surface in a closed loop.

Detection order for the local pages repo:
  1. --repo PATH override
  2. $GITHUB_PAGES_REPO env var
  3. scan immediate children of C:\\Users\\yaelm and C:\\æ for a git repo whose
     remote URL matches *.github.io (or a directory named *.github.io)
  4. if none found: create C:\\æ\\github-pages as a stub git repo
     (git init, .nojekyll, origin remote -> MYaelMendez.github.io, initial commit)

Usage:
  python deploy_github_pages.py [--dry-run] [--commit] [--push]
                                [--repo PATH] [--src PATH]
                                [--files neuromitosis.html aggregate.html]
                                [--trace]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

# --- defaults -------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = HERE                       # hermes-fork root (where the HTML lives)
DEFAULT_FILES = ["neuromitosis.html", "aggregate.html"]
DEFAULT_PAGES = r"C:\æ\github-pages"
PAGES_REMOTE = "https://github.com/MYaelMendez/MYaelMendez.github.io.git"
SCAN_ROOTS = [r"C:\Users\yaelm", r"C:\æ"]
META_CSV = r"C:\ae\meta_memory.csv"


def _git(args, cwd=None, check=True):
    """Run a git command, returning (rc, out). check=True raises on failure."""
    cmd = ["git"] + list(args)
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"git {args[0]} failed (rc={proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.returncode, proc.stdout.strip()


def _has_git() -> bool:
    return shutil.which("git") is not None


def _remote_is_pages(repo: str) -> bool:
    """Return True if repo's origin remote points at a *.github.io repo."""
    try:
        _, out = _git(["remote", "get-url", "origin"], cwd=repo, check=False)
    except Exception:
        return False
    return "github.io" in out.lower()


def _name_is_pages(name: str) -> bool:
    """Strong, unambiguous signal: the directory name itself names the repo."""
    n = name.lower()
    return (
        n == "github-pages"
        or n.endswith(".github.io")
        or "github-pages" in n
        or "github.io" in n
    )


def _looks_like_pages_dir(path: str) -> bool:
    """A directory is a pages repo if (a) its name names it, or (b) it is a
    git repo whose origin remote points at a *.github.io repo. The loose
    `index.html + .git` heuristic is intentionally dropped — a bare clone like
    C:\\Users\\yaelm\\Downloads backs up the github.io repo but is NOT the
    deploy target, so remote-name alone is too weak on its own (it still
    qualifies only when paired with the github.io name below)."""
    name = os.path.basename(path).lower()
    if _name_is_pages(name):
        return True
    if os.path.isdir(os.path.join(path, ".git")) and _remote_is_pages(path):
        return True
    return False


def _scan_for_repo() -> str | None:
    """Scan immediate children of each SCAN_ROOT for a pages repo.

    Priority: (1) an existing canonical C:\\æ\\github-pages, (2) children whose
    *name* names the pages repo, (3) children whose git *remote* points at
    github.io. Name-based matches are preferred so stray backup clones
    (e.g. a github.io clone sitting in Downloads) don't shadow the real one.
    """
    # (1) canonical path
    if os.path.isdir(DEFAULT_PAGES) and os.path.isdir(
        os.path.join(DEFAULT_PAGES, ".git")
    ):
        return DEFAULT_PAGES
    # (2)/(3) scan, name-based first then remote-based
    name_hits, remote_hits = [], []
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        try:
            children = sorted(os.listdir(root))
        except OSError:
            continue
        for child in children:
            cand = os.path.join(root, child)
            if not os.path.isdir(cand):
                continue
            n = child.lower()
            if _name_is_pages(n):
                name_hits.append(cand)
            elif os.path.isdir(os.path.join(cand, ".git")) and _remote_is_pages(cand):
                remote_hits.append(cand)
    if name_hits:
        return name_hits[0]
    if remote_hits:
        return remote_hits[0]
    return None


def detect_repo(explicit: str | None) -> str:
    """Find the pages repo, or return the default stub path if none exists."""
    if explicit:
        return os.path.abspath(explicit)
    env = os.environ.get("GITHUB_PAGES_REPO")
    if env:
        return os.path.abspath(env)
    found = _scan_for_repo()
    if found:
        return found
    return DEFAULT_PAGES  # caller decides create-vs-use


def create_stub_repo(path: str) -> None:
    """Init a stub github.io pages repo: .nojekyll + origin remote + initial commit."""
    os.makedirs(path, exist_ok=True)
    if not os.path.isdir(os.path.join(path, ".git")):
        _git(["init"], cwd=path)
    # .nojekyll so github.io serves the raw surfaces
    nojekyll = os.path.join(path, ".nojekyll")
    if not os.path.exists(nojekyll):
        with open(nojekyll, "w", encoding="utf-8") as fh:
            fh.write("")
    # set the origin remote (idempotent)
    rc, _ = _git(["remote", "get-url", "origin"], cwd=path, check=False)
    if rc != 0:
        _git(["remote", "add", "origin", PAGES_REMOTE], cwd=path)
    else:
        _git(["remote", "set-url", "origin", PAGES_REMOTE], cwd=path)
    # initial commit if repo has no commits yet
    rc, _ = _git(["rev-parse", "HEAD"], cwd=path, check=False)
    if rc != 0:
        _git(["add", "-A"], cwd=path)
        _git(
            ["commit", "-m",
             "init: github.io point-of-truth surface stub (nojekyll + origin)"],
            cwd=path,
        )
    print(f"[deploy] created stub pages repo @ {path}")


def copy_surfaces(src: str, repo: str, files: list[str], dry_run: bool) -> list[tuple[str, int]]:
    """Copy each source file into the repo root. Returns [(name, bytes), ...]."""
    copied = []
    for name in files:
        s = os.path.join(src, name)
        if not os.path.exists(s):
            print(f"[deploy] SKIP (missing source): {s}")
            continue
        d = os.path.join(repo, name)
        size = os.path.getsize(s)
        if dry_run:
            print(f"[deploy] would copy {name} ({size} bytes) -> {d}")
        else:
            shutil.copy2(s, d)
            print(f"[deploy] copied {name} ({size} bytes) -> {d}")
        copied.append((name, size))
    return copied


def commit(repo: str, files: list[str]) -> bool:
    """Stage + commit the deployed files if anything changed. Returns True if committed."""
    _git(["add", "--"] + files, cwd=repo)
    rc, _ = _git(["diff", "--cached", "--quiet"], cwd=repo, check=False)
    if rc == 0:
        print("[deploy] nothing staged to commit (already up to date)")
        return False
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    _git(["commit", "-m", f"deploy: {', '.join(files)} @ {ts}"], cwd=repo)
    print("[deploy] committed deploy surfaces")
    return True


def push(repo: str) -> None:
    """Push the current branch to origin."""
    _, branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)
    _git(["push", "origin", branch], cwd=repo)
    print(f"[deploy] pushed {branch} -> origin")


def trace_deploy(files: list[str]) -> None:
    """Record the deploy event into the cortex (meta_memory), mirroring the
    ingestor so the loop is closed. Lazy-import so the script works without
    the cortex module present."""
    try:
        sys.path.insert(0, HERE)
        from cortex_store import CortexStore  # type: ignore
        store = CortexStore()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        store.append("deploy", f"github.io -> {', '.join(files)} [{ts}]")
        print(f"[deploy] cortex trace: deployed {len(files)} surfaces")
    except Exception as e:  # pragma: no cover - best-effort only
        print(f"[deploy] cortex trace skipped: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy surfaces to local github.io pages repo")
    ap.add_argument("--repo", default=None, help="explicit pages repo path (skip detection)")
    ap.add_argument("--src", default=DEFAULT_SRC, help="source dir holding the HTML files")
    ap.add_argument("--files", nargs="+", default=DEFAULT_FILES,
                    help="files to copy (default: neuromitosis.html aggregate.html)")
    ap.add_argument("--dry-run", action="store_true", help="show actions without writing")
    ap.add_argument("--commit", action="store_true", help="git add + commit after copying")
    ap.add_argument("--push", action="store_true", help="git push to origin after commit")
    ap.add_argument("--trace", action="store_true",
                    help="append a deploy row to the meta_memory cortex")
    args = ap.parse_args()

    if not _has_git():
        print("[deploy] ERROR: git not found on PATH", file=sys.stderr)
        return 2

    repo = detect_repo(args.repo)
    existed = os.path.isdir(os.path.join(repo, ".git"))

    print(f"[deploy] pages repo target: {repo}")
    print(f"[deploy] source dir: {os.path.abspath(args.src)}")

    if not existed:
        if args.dry_run:
            print(f"[deploy] (dry-run) would create stub pages repo @ {repo}")
        else:
            create_stub_repo(repo)

    copied = copy_surfaces(os.path.abspath(args.src), repo, args.files, args.dry_run)

    if args.commit and not args.dry_run and copied:
        commit(repo, args.files)

    if args.push and not args.dry_run:
        push(repo)

    if args.trace and not args.dry_run:
        trace_deploy(args.files)

    print(f"[deploy] done. {len(copied)} surface(s) handled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
