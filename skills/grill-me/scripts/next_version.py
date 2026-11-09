#!/usr/bin/env python3
"""Pick the version and folder for a grill-me spec and plan pair.

Purpose: give every pair its own version, so parallel sessions never write two
different specs under one number. A pair lives in GitHub Spec Kit's folder
shape with a v prefix: specs/v007-topic/spec.md and specs/v007-topic/plan.md.
Rules:
- A linked worktree named for a version owns it: its branch's last segment, or
  else its folder's name, is `vN`, `vNNN` or `worktree-vN`. It reports a
  problem when another branch, worktree folder, reservation or spec folder
  also holds that version.
- `--version N` revises the pair that version N already has.
- Anywhere else the script reserves one past the highest version in use: any
  spec folder in the working tree or ever added on any branch, any branch or
  worktree folder named `vN` or `worktree-vN`, and any earlier reservation.
  It creates the ref refs/grill-me/vN, which every worktree shares and git
  creates only once, so two sessions running at once still get different
  numbers. Each such run uses up a number, so run it once per new pair.
- A version at or above CEILING marks a running list, such as v9999-todo, and
  never counts or gets reserved.
- Spec folders and files must not be symlinks, and a folder's name holds only
  a-z, 0-9 and dashes after its version, so the agent never writes through a
  link to somewhere else or passes a hostile name to a shell.
Usage: python3 scripts/next_version.py (--topic "short topic" | --version N) [--dir specs]
Output: one JSON object: version, source, folder, spec, plan, existing, and
problem, which is null unless the agent must stop and ask.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

VERSION_NAME = re.compile(r"^(?:worktree-)?v(\d+)$")
FOLDER_VERSION = re.compile(r"^v(\d+)-")
SAFE_FOLDER = re.compile(r"^v\d+-[a-z0-9-]+$")
RESERVED = "refs/grill-me/"
CEILING = 9000
TOPIC_WORDS = 6


def git(root: str, *args: str, stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run(["git", "-C", root, *args], input=stdin, capture_output=True, text=True)
    if check and done.returncode:
        sys.exit(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done


def lines(root: str, *args: str) -> list[str]:
    return [line for line in git(root, *args).stdout.splitlines() if line]


def has_ref(root: str, ref: str) -> bool:
    return git(root, "rev-parse", "--verify", "-q", ref, check=False).returncode == 0


def slug(topic: str) -> str:
    words = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-").split("-")
    return "-".join(words[:TOPIC_WORDS])


def version_of(pattern: re.Pattern, path: str) -> int | None:
    """The version a name or folder holds, judged on its last path segment."""
    match = pattern.match(path.rstrip("/").rsplit("/", 1)[-1])
    return version if match and (version := int(match[1])) < CEILING else None


def holding(pattern: re.Pattern, names, version: int) -> list[str]:
    return sorted(n for n in names if version_of(pattern, n) == version)


def inside(root: str, path: str) -> bool:
    """Whether a path stays in the repository once every symlink is resolved."""
    base = os.path.realpath(root)
    return os.path.commonpath([os.path.realpath(os.path.join(root, path)), base]) == base


def tree_folders(root: str, specs: str) -> set[str]:
    """Spec folders on disk, so a pair written but not yet committed still counts."""
    full = os.path.join(root, specs)
    names = os.listdir(full) if os.path.isdir(full) else []
    return {f"{specs}/{n}" for n in names if os.path.isdir(os.path.join(full, n))}


def added_folders(root: str, specs: str, *revs: str) -> set[str]:
    """Spec folders that gained a file in the given commits; renames count as adds of the new path.

    -z keeps git from quoting names that hold non-ASCII characters, so every folder counts.
    """
    out = git(root, "log", *revs, "--no-renames", "--diff-filter=A", "--format=", "--name-only", "-z", "--", specs).stdout
    folders = set()
    for path in out.split("\0"):
        head, sep, _ = path.strip("\n").removeprefix(f"{specs}/").partition("/")
        if sep:
            folders.add(f"{specs}/{head}")
    return folders


def live_worktrees(root: str) -> list[str]:
    """Every worktree folder git lists, the main checkout first, without those already deleted."""
    folders = []
    for line in lines(root, "worktree", "list", "--porcelain"):
        if line.startswith("worktree "):
            folders.append(os.path.realpath(line[len("worktree "):]))
        elif line.startswith("prunable"):
            folders.pop()  # its folder is gone, so it holds nothing
    return folders


def linked(root: str) -> bool:
    """Whether this checkout is a linked worktree rather than the main checkout."""
    git_dir, common = lines(root, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir")
    return os.path.realpath(git_dir) != os.path.realpath(common)


def holders(root: str) -> list[str]:
    """Branch and reservation refs and live worktree folders: everything that can hold a version."""
    return lines(root, "for-each-ref", "--format=%(refname)", "refs/heads", RESERVED) + live_worktrees(root)


def reserve(root: str, version: int, topic: str) -> int:
    """Create refs/grill-me/vN, moving up until git accepts one no other session holds."""
    note = git(root, "hash-object", "-w", "--stdin", stdin=f"{topic}\n").stdout.strip()
    waits = 100
    while version < CEILING:
        done = git(root, "update-ref", f"{RESERVED}v{version}", note, "", check=False)
        if done.returncode == 0:
            return version
        if has_ref(root, f"{RESERVED}v{version}"):
            version += 1
        elif ".lock': File exists" in done.stderr and waits:
            waits -= 1
            time.sleep(0.05)  # another session holds the ref lock; try the same number again
        else:
            sys.exit(f"cannot reserve v{version}: {done.stderr.strip()}")
    sys.exit(f"no free version below v{CEILING}, where running lists start")


def owned_version(root: str, branch: str) -> tuple[int | None, str]:
    """The version a linked worktree's branch or folder name claims; a main checkout claims none."""
    if linked(root):
        for source, name in (("branch", branch), ("folder", root)):
            if (version := version_of(VERSION_NAME, name)) is not None:
                return version, source
    return None, "next"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    want = parser.add_mutually_exclusive_group(required=True)
    want.add_argument("--topic", help="two to six words naming the work")
    want.add_argument("--version", type=int, help="revise the pair this version already has")
    parser.add_argument("--dir", default="specs", help="the folder that holds one subfolder per pair")
    args = parser.parse_args()

    root = git(os.getcwd(), "rev-parse", "--show-toplevel").stdout.strip()
    specs = os.path.normpath(args.dir)
    if os.path.isabs(specs) or specs == "." or not inside(root, specs):
        sys.exit(f"{args.dir} must be a folder below the repository root")
    topic = slug(args.topic or "")
    if args.topic is not None and not topic:
        sys.exit("the topic needs at least one letter or digit from a-z or 0-9")

    here = tree_folders(root, specs)
    branch = git(root, "branch", "--show-current").stdout.strip()
    problem = None

    if args.version is not None:
        version, source = args.version, "given"
    else:
        version, source = owned_version(root, branch)
        if version is None:
            used = [version_of(FOLDER_VERSION, f) for f in here | added_folders(root, specs, "--all")]
            used += [version_of(VERSION_NAME, n) for n in holders(root)]
            version = reserve(root, max((v for v in used if v is not None), default=0) + 1, topic)
        else:
            # A `vN` folder still owns its `worktree-vN` branch, the pair `claude -w vN` makes, after a branch switch.
            own = {f"refs/heads/{branch}", f"refs/heads/worktree-v{version}", os.path.realpath(root)}
            others = [n for n in holding(VERSION_NAME, holders(root), version) if n not in own]
            if has_ref(root, "HEAD"):
                others += holding(FOLDER_VERSION, added_folders(root, specs, "--all", "--not", "HEAD") - here, version)
            if others:
                problem = f"v{version} is already held by: {', '.join(others)}"

    existing = holding(FOLDER_VERSION, here, version)
    folder = None
    if problem is None:
        if len(existing) > 1:
            problem = f"several folders hold v{version}: {', '.join(existing)}"
        elif existing and not SAFE_FOLDER.match(os.path.basename(existing[0])):
            problem = f"spec folder names may hold only a-z, 0-9 and dashes after the version: {existing[0]}"
        elif existing:
            folder = existing[0]
        elif topic:
            folder = f"{specs}/v{version:03d}-{topic}"
        else:
            problem = f"v{version} has no spec folder yet; pass --topic to name a new one"
    spec, plan = (f"{folder}/spec.md", f"{folder}/plan.md") if folder else (None, None)
    symlinked = [p for p in (folder, spec, plan) if p and os.path.islink(os.path.join(root, p))]
    if symlinked:
        folder, spec, plan = None, None, None
        problem = f"spec folders and files must not be symlinks: {', '.join(symlinked)}"
    print(json.dumps({"version": version, "source": source, "folder": folder, "spec": spec, "plan": plan,
                      "existing": existing, "problem": problem}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
