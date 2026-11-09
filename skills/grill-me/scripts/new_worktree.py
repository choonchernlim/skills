#!/usr/bin/env python3
"""Create the worktree a grill-me plan moves into, or say whether to offer one.

Purpose: give a large plan its own worktree, cut from the current branch, in the
shape `claude -w vN` uses: folder .claude/worktrees/vN on branch worktree-vN.
Rules:
- `--check` says whether to offer a worktree: only outside a linked worktree,
  and only where worktrees are used, meaning .claude/worktrees/ is git-ignored
  or another live worktree exists.
- `--topic T` reserves the next version with next_version.py; `--version N`
  uses a version the run already has. Either refuses inside a linked worktree,
  or when the folder or branch already exists.
- It fetches the branch's upstream, and cuts from it when the branch is only
  behind, so the worktree starts current without touching this checkout. When
  the fetch fails or the branch has diverged, it warns and cuts from HEAD.
  With --carry it always cuts from HEAD, which the carried edits are against.
- Inside Herdr (HERDR_ENV=1, and its pane answers), Herdr creates the worktree,
  so it gets a sidebar workspace; when that fails, it stops and says why.
- It records the branch it was cut from as branch.worktree-vN.parent, deletes
  the reservation refs/grill-me/vN, since the folder now holds N, and adds
  .claude/worktrees/ to .git/info/exclude when nothing ignores it yet.
- `--carry PATH...` copies uncommitted changes under those paths into the new
  worktree, then resets them here; staged changes arrive unstaged. It refuses a
  file with both staged and unstaged edits, a non-regular file, and a target
  reached through a symlink, before moving anything. It never uses git stash,
  which every worktree shares, and reads names literally, never as globs.
- Every failure is reported as JSON, freeing a version it reserved.
Usage: python3 scripts/new_worktree.py (--check | (--topic T | --version N) [--carry PATH ...] [--agent KIND])
Output: one JSON object. `--check` prints offer. Otherwise: version, path,
branch, method (git or herdr), spec and plan (paths inside path), handoff (a
Herdr command to run once the pair is written, or null), carried, warnings,
and problem, which is null unless the agent must stop and ask.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True  # importing the sibling script must leave no __pycache__ in an installed skill
from next_version import RESERVED, git, has_ref, inside, linked, live_worktrees

WORKTREES = ".claude/worktrees"
NEXT_VERSION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "next_version.py")


def out(root: str, *args: str) -> str:
    return git(root, *args).stdout.strip()


def succeeds(root: str, *args: str) -> bool:
    return git(root, *args, check=False).returncode == 0


def herdr(*args: str, timeout: int) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def in_herdr() -> bool:
    if os.environ.get("HERDR_ENV") != "1":
        return False
    done = herdr("pane", "current", "--current", timeout=5)
    return done is not None and done.returncode == 0


def ignored(root: str) -> bool:
    return succeeds(root, "check-ignore", "-q", f"{WORKTREES}/")


def offer(root: str) -> bool:
    return not linked(root) and (ignored(root) or len(live_worktrees(root)) > 1)


def exclude(root: str) -> None:
    """Ignore worktree folders in this clone only, through .git/info/exclude, when nothing ignores them yet."""
    if ignored(root):
        return
    path = os.path.join(out(root, "rev-parse", "--path-format=absolute", "--git-common-dir"), "info", "exclude")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(("" if not text or text.endswith("\n") else "\n") + f"{WORKTREES}/\n")


def next_version(cwd: str, *args: str) -> dict:
    done = subprocess.run([sys.executable, NEXT_VERSION, *args], cwd=cwd, capture_output=True, text=True)
    if done.returncode:
        return {"problem": f"next_version.py failed: {done.stderr.strip()}"}
    return json.loads(done.stdout)


def base_commit(root: str, branch: str, warnings: list) -> str:
    """The upstream commit when this branch is only behind it, else HEAD."""
    head = out(root, "rev-parse", "HEAD")
    remote = git(root, "config", f"branch.{branch}.remote", check=False).stdout.strip() if branch else ""
    merge = git(root, "config", f"branch.{branch}.merge", check=False).stdout.strip() if branch else ""
    if not (remote and merge):
        return head
    try:
        # No terminal and no stdin, so an ssh or credential prompt fails at once instead of waiting for a reply.
        fetched = subprocess.run(["git", "-C", root, "fetch", "--quiet", remote, merge], capture_output=True,
                                 text=True, timeout=120, stdin=subprocess.DEVNULL, start_new_session=True,
                                 env=os.environ | {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"})
        failure = fetched.stderr.strip() if fetched.returncode else None
    except subprocess.TimeoutExpired:
        failure = "timed out"
    if failure is not None:
        warnings.append(f"fetching {remote} failed, so the worktree starts at HEAD: {failure}")
        return head
    upstream = git(root, "rev-parse", "--verify", "-q", "@{upstream}", check=False).stdout.strip()
    if not upstream:
        warnings.append(f"{branch} keeps no remote-tracking copy of its upstream, so the worktree starts at HEAD")
        return head
    if succeeds(root, "merge-base", "--is-ancestor", head, upstream):
        return upstream
    if not succeeds(root, "merge-base", "--is-ancestor", upstream, head):
        warnings.append(f"{branch} and its upstream have diverged, so the worktree starts at HEAD")
    return head


def changes(root: str, paths: list[str]) -> list[tuple[str, str, bool]]:
    """Uncommitted paths under the given ones, each with its two-letter status and whether it exists here.

    --literal-pathspecs keeps a name such as app/[id]/page.tsx from matching other files as a glob.
    """
    listed = git(root, "--literal-pathspecs", "status", "--porcelain=v1", "-z", "--no-renames",
                 "--untracked-files=all", "--", *paths).stdout
    return [(entry[3:], entry[:2], os.path.lexists(os.path.join(root, entry[3:])))
            for entry in filter(None, listed.split("\0"))]


def uncarriable(root: str, path: str, moved: list[tuple[str, str, bool]]) -> str | None:
    """Why the move must not start: edits it would lose, a source that is not a regular file, or a symlinked target."""
    for rel, status, exists in moved:
        source, target = os.path.join(root, rel), os.path.join(path, rel)
        if status[0] not in " ?" and status[1] != " ":
            return f"cannot carry {rel}: it has staged and unstaged edits; stage or drop one of them first"
        if exists and (os.path.islink(source) or not os.path.isfile(source)):
            return f"cannot carry {rel}: only regular files move"
        if os.path.islink(target) or not inside(path, os.path.dirname(rel) or "."):
            return f"cannot carry {rel}: the worktree holds a symlink on its path"
    return None


def carry(root: str, path: str, moved: list[tuple[str, str, bool]]) -> list[str]:
    """Copy each change into the worktree, then reset it here; staged changes arrive unstaged."""
    for rel, _, exists in moved:
        source, target = os.path.join(root, rel), os.path.join(path, rel)
        if exists:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(source, target)
        elif os.path.lexists(target):
            os.remove(target)
    tracked = sorted(rel for rel, status, _ in moved if status != "??")
    if tracked:
        git(root, "--literal-pathspecs", "restore", "--source=HEAD", "--staged", "--worktree",
            "--pathspec-from-file=-", "--pathspec-file-nul", stdin="\0".join(tracked))
    for rel, status, exists in moved:
        if exists and status == "??":
            os.remove(os.path.join(root, rel))
            prune(root, os.path.dirname(rel))
    return [rel for rel, _, _ in moved]


def prune(root: str, rel: str) -> None:
    """Remove folders the move left empty, stopping at the first one that still holds something."""
    while rel and not os.listdir(os.path.join(root, rel)):
        os.rmdir(os.path.join(root, rel))
        rel = os.path.dirname(rel)


def refusal(root: str, paths: list[str]) -> str | None:
    if linked(root):
        return "this is already a linked worktree; plan here instead"
    kept_out = os.path.realpath(os.path.join(root, WORKTREES))
    for rel in paths:
        full = os.path.realpath(os.path.join(root, rel))
        if not inside(root, rel) or os.path.commonpath([full, kept_out]) == kept_out:
            return f"--carry paths must stay in this checkout, outside {WORKTREES}: {rel}"
    return None


def create(root: str, topic: str | None, version: int | None, paths: list[str], agent: str) -> dict:
    result = {"version": version, "path": None, "branch": None, "method": None, "spec": None, "plan": None,
              "handoff": None, "carried": [], "warnings": [], "problem": refusal(root, paths)}
    if result["problem"]:
        return result
    if topic is not None:
        reserved = next_version(root, "--topic", topic)
        if reserved.get("problem"):
            result["problem"] = reserved["problem"]
            return result
        version = result["version"] = reserved["version"]
    branch, rel_path = f"worktree-v{version}", f"{WORKTREES}/v{version}"
    path = result["path"] = os.path.join(root, rel_path)
    result["branch"] = branch

    def stop(problem: str) -> dict:
        """Report a problem, freeing a version this call reserved so the number is not lost."""
        if topic is not None:
            git(root, "update-ref", "-d", f"{RESERVED}v{version}", check=False)
        result["problem"] = problem
        return result

    if os.path.lexists(path):
        return stop(f"{rel_path} already exists")
    if has_ref(root, f"refs/heads/{branch}"):
        return stop(f"branch {branch} already exists")
    try:
        return build(root, topic, version, paths, agent, result, stop)
    except (SystemExit, OSError) as error:  # a failed git call exits; report it as JSON and free the version
        return stop(str(error))


def herdr_name(root: str, version: int) -> str:
    """An agent name unique across every repository one Herdr server sees: the repository's name, then vN."""
    repo = re.sub(r"[^a-z0-9-]+", "-", os.path.basename(root).lower()).strip("-")[:24] or "repo"
    return f"{repo if repo[0].isalpha() else 'r-' + repo}-v{version}"[:32]


def build(root: str, topic: str | None, version: int, paths: list[str], agent: str, result: dict, stop) -> dict:
    branch, path = result["branch"], result["path"]
    rel_path = os.path.relpath(path, root)
    current = out(root, "branch", "--show-current")
    if not current:
        result["warnings"].append("HEAD is detached, so no parent branch is recorded")
    # Carried files were edited against HEAD; cutting from a newer upstream would revert its changes to them.
    base = out(root, "rev-parse", "HEAD") if paths else base_commit(root, current, result["warnings"])
    exclude(root)

    pane = None
    if in_herdr():
        made = herdr("worktree", "create", "--cwd", root, "--branch", branch, "--base", base,
                     "--path", path, "--label", f"v{version}", "--no-focus", timeout=60)
        if made is None or made.returncode:
            reason = "herdr not found or timed out" if made is None else made.stderr.strip() or made.stdout.strip()
            return stop(f"herdr worktree create failed: {reason}")
        result["method"] = "herdr"
        try:
            pane = json.loads(made.stdout)["result"]["root_pane"]["pane_id"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pane = None
        if not isinstance(pane, str) or not pane:
            pane = None
            result["warnings"].append(f"herdr did not report the workspace's pane; start an agent in workspace v{version} yourself")
    else:
        git(root, "worktree", "add", "-q", "-b", branch, path, base)
        result["method"] = "git"
    if os.path.realpath(path) not in live_worktrees(root):
        return stop(f"{rel_path} is not a git worktree after creating it")

    if current:
        git(root, "config", f"branch.{branch}.parent", current)
    git(root, "update-ref", "-d", f"{RESERVED}v{version}", check=False)
    if paths:
        moved = changes(root, paths)
        if (problem := uncarriable(root, path, moved)) is not None:
            result["problem"] = f"{problem}; the worktree exists, but nothing moved"
            return result
        result["carried"] = carry(root, path, moved)
    pair = next_version(path, *(["--topic", topic] if topic is not None else ["--version", str(version)]))
    if pair.get("problem"):
        result["problem"] = pair["problem"]
        return result
    # Absolute, so an agent running from the main checkout writes the pair into the worktree.
    result.update(spec=os.path.join(path, pair["spec"]), plan=os.path.join(path, pair["plan"]))
    if pane:
        name = herdr_name(root, version)
        result["handoff"] = (f"herdr agent start {name} --kind {shlex.quote(agent)} --pane {shlex.quote(pane)} && "
                             f"herdr agent prompt {name} {shlex.quote('/grill-me resume ' + pair['spec'])}")
    return result


def positive(text: str) -> int:
    if not text.isdigit() or int(text) < 1:
        raise argparse.ArgumentTypeError("the version must be a whole number of 1 or more")
    return int(text)


def agent_kind(text: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]*", text):
        raise argparse.ArgumentTypeError("an agent kind is lower-case letters, digits and dashes, such as claude")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    want = parser.add_mutually_exclusive_group(required=True)
    want.add_argument("--check", action="store_true", help="say whether to offer a worktree")
    want.add_argument("--topic", help="reserve the next version for a new pair with this topic")
    want.add_argument("--version", type=positive, help="use the version this run already has")
    parser.add_argument("--carry", nargs="+", default=[], metavar="PATH", help="move uncommitted changes under these paths")
    parser.add_argument("--agent", default="claude", type=agent_kind, help="the Herdr agent kind that continues in the worktree")
    args = parser.parse_args()
    if args.check and args.carry:
        parser.error("--carry needs --topic or --version")

    root = out(os.getcwd(), "rev-parse", "--show-toplevel")
    found = {"offer": offer(root)} if args.check else create(root, args.topic, args.version, args.carry, args.agent)
    print(json.dumps(found, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
