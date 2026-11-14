#!/usr/bin/env python3
"""Merge a finished worktree branch into its remote feature branch.

Purpose: build a fresh base (the remote feature branch with its remote parent
merged in), rebase the worktree onto it, and after the review gate merge it
with --no-ff and push, so a worktree reaches the feature branch only as one
reviewed merge, and a push that lost a race loses nothing.
Usage: run inside the worktree, or name it with --worktree PATH. Run the file
itself, not through python3, so one narrow permission rule can approve it.
  merge_worktree.py [--worktree PATH] prepare [--parent BRANCH]
  merge_worktree.py [--worktree PATH] continue [--clash "PATH: WHY"]...
  merge_worktree.py [--worktree PATH] abort
  merge_worktree.py [--worktree PATH] land --tip SHA [--title TEXT] [--no-verify]
  merge_worktree.py [--worktree PATH] cleanup
Output: one JSON object. `status` is one of refused, needs-parent, conflict,
merged, ready, aborted, stale, rejected, landed, removed or removing; with
`problem`, `warnings`, and the facts each status needs. Exit 0 unless the
arguments are wrong. Needs git 2.32 or later.

Branches are never named here. The feature branch is `branch.<worktree>.parent`
in git config, else the main checkout's branch. Its parent is
`branch.<feature>.parent`, which `prepare --parent` stores once.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys

STATE = "merge-worktree.json"
FINISH_LOG = "merge-worktree-finish.log"
FINISH_JOB = "merge-worktree-finish.json"
TRAILER = "Clash-resolved"
NETWORK = 120
MIN_GIT = (2, 32)
# Never prompt for credentials or messages: a prompt would hang an agent's shell.
QUIET = {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never", "GIT_EDITOR": "true"}
# Replay recorded resolutions, but never stage them: each one still waits for the agent's check.
RERERE = ("-c", "rerere.enabled=true", "-c", "rerere.autoUpdate=false")
END = "--end-of-options"


class Stop(Exception):
    """Ends a command with a status other than success; `facts` join the output."""

    def __init__(self, status: str, problem: str | None = None, **facts):
        super().__init__(problem or status)
        self.status, self.problem, self.facts = status, problem, facts


def run(*args: str, cwd: str = ".", network: bool = False) -> subprocess.CompletedProcess:
    """Run git in its own session, with no terminal to prompt on; a network call is killed whole on timeout."""
    process = subprocess.Popen(["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL, text=True, env=os.environ | QUIET, start_new_session=True)
    try:
        out, err = process.communicate(timeout=NETWORK if network else None)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise Stop("refused", f"git {args[0]} timed out after {NETWORK}s") from None
    return subprocess.CompletedProcess(process.args, process.returncode, out, err)


def why(done: subprocess.CompletedProcess) -> str:
    return (done.stderr or done.stdout).strip()


def git(*args: str, cwd: str = ".", network: bool = False, failed: str | None = None) -> str:
    done = run(*args, cwd=cwd, network=network)
    if done.returncode:
        raise Stop("refused", f"{failed or 'git ' + ' '.join(args)} failed: {why(done)}")
    return done.stdout.strip()


def ancestor(older: str, newer: str) -> bool:
    return run("merge-base", "--is-ancestor", END, older, newer).returncode == 0


def current_branch() -> str | None:
    done = run("symbolic-ref", "--short", "-q", "HEAD")
    return done.stdout.strip() or None if done.returncode == 0 else None


def safe_branch(name: str) -> bool:
    return not name.startswith("-") and run("check-ref-format", "--branch", name).returncode == 0


class Repo:
    """This worktree's folders and the branch config, read once per command."""

    def __init__(self):
        found = re.search(r"(\d+)\.(\d+)", run("version").stdout)
        if not found or tuple(map(int, found.groups())) < MIN_GIT:
            raise Stop("refused", f"git {'.'.join(map(str, MIN_GIT))} or later is needed")
        self.git_dir, self.common_dir, self.root = git(
            "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir", "--show-toplevel").splitlines()
        listed = run("config", "-z", "--get-regexp", r"^branch\.").stdout
        self.config = dict(entry.split("\n", 1) for entry in listed.split("\0") if "\n" in entry)

    def path(self, name: str) -> str:
        return os.path.join(self.git_dir, name)

    def stopped(self) -> str | None:
        """`merge` or `rebase` while one is stopped on a conflict here, else None."""
        if os.path.exists(self.path("MERGE_HEAD")):
            return "merge"
        if any(os.path.isdir(self.path(name)) for name in ("rebase-merge", "rebase-apply")):
            return "rebase"
        return None

    def load(self) -> dict:
        try:
            with open(self.path(STATE), encoding="utf-8") as handle:
                state = json.load(handle)
        except (OSError, ValueError):
            return {}
        return state if isinstance(state, dict) else {}

    def save(self, **state) -> None:
        with open(self.path(STATE), "w", encoding="utf-8") as handle:
            json.dump(state, handle)

    def forget(self) -> None:
        if os.path.exists(self.path(STATE)):
            os.remove(self.path(STATE))


def changed(*flags: str) -> list[tuple[str, str]]:
    """(status, path) for each entry `git status` reports; a rename or copy lists its new path once."""
    entries, found, source_next = run("status", "--porcelain=v1", "-z", *flags).stdout.split("\0"), [], False
    for entry in entries:
        if source_next or not entry:
            source_next = False
            continue
        found.append((entry[:2], entry[3:]))
        source_next = entry[0] in "RC"
    return found


def dirty() -> list[str]:
    return [path for _, path in changed("--untracked-files=all")]


def nested_repos(root: str, folders: list[str]) -> list[str]:
    """Repositories and worktrees inside these ignored folders; removing the worktree would lose their work."""
    found = []
    for folder in folders:
        for here, dirs, files in os.walk(os.path.join(root, folder)):
            if ".git" in dirs or ".git" in files:
                found.append(os.path.relpath(here, root) + "/")
                dirs.clear()
    return found


def unmerged() -> list[str]:
    return git("diff", "--name-only", "--diff-filter=U").splitlines()


def main_checkout() -> tuple[str, str | None]:
    """The main checkout's folder and its branch; the first `worktree list` entry is always it."""
    path, branch = None, None
    for line in git("worktree", "list", "--porcelain").splitlines():
        if not line:
            break
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch refs/heads/"):
            branch = line[len("branch refs/heads/"):]
    return path, branch


def where(repo: Repo, ask: bool = True, branch: str | None = None, parent: str | None = None) -> dict:
    """The worktree's branch, feature branch, remote and the feature's parent, or a Stop.

    `branch` names the worktree branch while a stopped merge or rebase detaches HEAD.
    `parent` overrides the stored parent, for `prepare --parent`.
    """
    if repo.git_dir == repo.common_dir:
        raise Stop("refused", "this is the main checkout; run it inside the worktree to merge")
    branch = branch or current_branch()
    if not branch:
        raise Stop("refused", "HEAD is detached; switch to the worktree's branch first")
    main, main_branch = main_checkout()
    recorded = repo.config.get(f"branch.{branch}.parent")
    feature = recorded or main_branch
    if not feature or feature == branch:
        raise Stop("refused", f"no feature branch for {branch}: set it with "
                              f"git config branch.{branch}.parent <feature>")
    remote, merge = repo.config.get(f"branch.{feature}.remote"), repo.config.get(f"branch.{feature}.merge")
    if not remote or remote == "." or not merge:
        raise Stop("refused", f"{feature} has no upstream on a remote; push it with git push -u <remote> {feature}")
    upstream = merge.removeprefix("refs/heads/")
    default = run("symbolic-ref", "--short", "-q", f"refs/remotes/{remote}/HEAD").stdout.strip().removeprefix(f"{remote}/")
    if not recorded and upstream == default:
        raise Stop("refused", f"{branch} records no feature branch, and the main checkout's {feature} pushes to "
                              f"{remote}/{default}, the default branch; set git config branch.{branch}.parent <feature>")
    if parent and (parent in (feature, branch) or not safe_branch(parent)):
        raise Stop("refused", f"{parent!r} cannot be the parent of {feature}")
    parent = parent or repo.config.get(f"branch.{feature}.parent")
    if not parent and ask:
        raise Stop("needs-parent", f"{feature} has no parent branch recorded; ask which branch it merges from",
                   feature=feature, suggest=default or None)
    return {"branch": branch, "feature": feature, "upstream": upstream, "remote": remote, "parent": parent,
            "main": main, "start": f"refs/remotes/{remote}/{upstream}",
            "parent_ref": f"refs/remotes/{remote}/{parent}" if parent else None}


def fetch(spot: dict, *names: str) -> None:
    """Fetch each branch into its remote-tracking ref, whatever the remote's own fetch refspec covers."""
    specs = [f"+refs/heads/{name}:refs/remotes/{spot['remote']}/{name}" for name in names]
    git("fetch", "--quiet", "--no-tags", END, spot["remote"], *specs, network=True, failed=f"fetching {spot['remote']}")


def own_branch(repo: Repo, state: dict) -> str:
    """The worktree branch recorded at a conflict, checked against git's own record of it."""
    branch = state.get("branch")
    if not isinstance(branch, str) or not safe_branch(branch) or run(
            "rev-parse", "-q", "--verify", f"refs/heads/{branch}").returncode:
        raise Stop("refused", "the saved merge state names no branch here; run abort, then prepare")
    head_name = repo.path(os.path.join("rebase-merge", "head-name"))
    if os.path.exists(head_name):
        with open(head_name, encoding="utf-8") as handle:
            if handle.read().strip() != f"refs/heads/{branch}":
                raise Stop("refused", "the stopped rebase is not on the saved branch; run abort, then prepare")
    return branch


def conflict(repo: Repo, spot: dict, phase: str, base: str | None) -> Stop:
    files = unmerged()
    repo.save(phase=phase, base=base, branch=spot["branch"], files=files)
    remaining = run(*RERERE, "rerere", "remaining").stdout.splitlines()
    return Stop("conflict", None, phase=phase, files=files, replayed=[name for name in files if name not in remaining])


def undo(kind: str, branch: str, done: subprocess.CompletedProcess, what: str) -> Stop:
    """Back out a failed merge or rebase that did not stop on a conflict, and say why."""
    run(kind, "--abort")
    run("switch", "-q", END, branch)
    return Stop("refused", f"{what} failed: {why(done)}")


def rebase(repo: Repo, spot: dict, base: str) -> dict:
    """Rebase the worktree branch onto `base`, then report the packet's facts."""
    if current_branch() != spot["branch"]:
        git("switch", "-q", END, spot["branch"])
    if not ancestor(base, "HEAD"):
        done = run(*RERERE, "rebase", "--no-autosquash", END, base)
        if done.returncode:
            if repo.stopped() == "rebase" and unmerged():
                raise conflict(repo, spot, "rebase", base)
            raise undo("rebase", spot["branch"], done, "rebase")
    return ready(repo, spot, base)


def clash_notes(*ranges: str) -> list[str]:
    out = git("log", f"--format=%(trailers:key={TRAILER},valueonly,unfold)", *ranges)
    return [line.strip() for line in out.splitlines() if line.strip()]


def ready(repo: Repo, spot: dict, base: str) -> dict:
    tip, start = git("rev-parse", "HEAD"), git("rev-parse", spot["start"])
    repo.save(phase="ready", base=base, tip=tip, start=start, branch=spot["branch"])
    added = removed = 0
    for line in git("diff", "--numstat", base, tip).splitlines():
        plus, minus, _ = line.split("\t", 2)
        added += int(plus) if plus.isdigit() else 0
        removed += int(minus) if minus.isdigit() else 0
    files = git("diff", "--name-status", base, tip).splitlines()
    # This worktree's notes, plus the base merge's own; never the notes already in the parent's history.
    clashes = clash_notes(f"{base}..{tip}") + (clash_notes("--no-walk", base) if base != start else [])
    return {
        "status": "ready", "branch": spot["branch"], "feature": spot["feature"], "parent": spot["parent"],
        "target": f"{spot['remote']}/{spot['upstream']}", "base": base, "tip": tip,
        "commits": int(git("rev-list", "--count", f"{base}..{tip}")),
        "parent_commits": int(git("rev-list", "--count", "--no-merges", f"{start}..{base}")),
        "added": added, "removed": removed, "files": files, "clashes": clashes,
        "pair": pair(repo, files),
    }


def pair(repo: Repo, files: list[str]) -> dict | None:
    """The spec and plan folder the worktree changed, and how many plan steps are still open."""
    for entry in files:
        path = entry.split("\t")[-1]
        folder, plan = os.path.dirname(path), os.path.join(repo.root, path)
        if (os.path.basename(path) == "plan.md" and os.path.isfile(plan)
                and os.path.isfile(os.path.join(repo.root, folder, "spec.md"))):
            with open(plan, encoding="utf-8") as handle:
                return {"folder": folder, "open_steps": sum(line.lstrip().startswith("- [ ]") for line in handle)}
    return None


def prepare(repo: Repo, args) -> dict:
    stopped = repo.stopped()
    if stopped:
        raise Stop("refused", f"a {stopped} is stopped on a conflict; resolve it and run continue, or run abort",
                   files=unmerged())
    spot = where(repo, parent=args.parent)
    files = dirty()
    if files:
        raise Stop("refused", "the worktree has uncommitted changes, which nobody reviewed; commit or remove them",
                   files=files)
    fetch(spot, spot["upstream"], spot["parent"])
    if args.parent:
        git("config", f"branch.{spot['feature']}.parent", args.parent)
    if ancestor("HEAD", spot["start"]):
        raise Stop("merged", f"{spot['branch']} is already in {spot['remote']}/{spot['upstream']}; run cleanup")
    if ancestor(spot["parent_ref"], spot["start"]):
        return rebase(repo, spot, git("rev-parse", spot["start"]))
    git("switch", "-q", "--detach", END, spot["start"])
    done = run(*RERERE, "merge", "--no-ff", "--no-edit", "-m",
               f"Merge {spot['parent']} into {spot['feature']}", END, spot["parent_ref"])
    if done.returncode:
        if repo.stopped() == "merge" and unmerged():
            raise conflict(repo, spot, "base", None)
        raise undo("merge", spot["branch"], done, f"merging {spot['parent']}")
    return rebase(repo, spot, git("rev-parse", "HEAD"))


def resume(repo: Repo, args) -> dict:
    state, stopped = repo.load(), repo.stopped()
    if state.get("phase") not in ("base", "rebase") or not stopped:
        raise Stop("refused", "no conflict from prepare is open here; run prepare")
    spot = where(repo, branch=own_branch(repo, state))
    files = unmerged()
    if files:
        raise Stop("refused", "some files are still unmerged; resolve them and git add each", files=files)
    unstaged = git("diff", "--name-only").splitlines()
    if unstaged:
        raise Stop("refused", "some resolved files are not staged; git add each", files=unstaged)
    staged = git("diff", "--cached", "--name-only").splitlines()
    conflicted = set(state.get("files") or [])
    check = run("diff", "--cached", "--check").stdout.splitlines()
    marked = sorted({line.split(":", 1)[0] for line in check if "leftover conflict marker" in line} & conflicted)
    if marked:
        raise Stop("refused", "conflict markers are still in staged files", files=marked)
    trailers = [arg for clash in args.clash for arg in ("--trailer", f"{TRAILER}: {clash}")]
    warnings = []
    if stopped == "rebase" and not staged and not trailers:
        warnings.append("the resolution left this commit empty, so it was dropped")
        done = run(*RERERE, "rebase", "--skip")
    elif stopped == "rebase":
        # Keep the stopped commit's author and message; an empty resolution keeps its notes as an empty commit.
        git(*RERERE, "commit", "-q", "-C", "REBASE_HEAD", "--allow-empty", *trailers)
        done = run(*RERERE, "rebase", "--continue")
    else:
        git(*RERERE, "commit", "-q", "--no-edit", *trailers)
        done = None
    if done is not None and done.returncode:
        if repo.stopped() == "rebase" and unmerged():
            raise conflict(repo, spot, "rebase", state.get("base"))
        raise Stop("refused", f"rebase failed: {why(done)}")
    result = rebase(repo, spot, git("rev-parse", "HEAD")) if state["phase"] == "base" else ready(repo, spot, state["base"])
    result["warnings"] = warnings
    return result


def abort(repo: Repo, _args) -> dict:
    state, stopped = repo.load(), repo.stopped()
    # Only a conflict prepare stopped on is ours to throw away; any other merge or rebase is the user's.
    if state.get("phase") not in ("base", "rebase"):
        raise Stop("refused", "nothing to abort: no prepare is stopped on a conflict here")
    branch = own_branch(repo, state) if state.get("branch") else None
    if stopped:
        run(stopped, "--abort")
    if branch:
        run("switch", "-q", END, branch)
    repo.forget()
    return {"status": "aborted", "branch": current_branch()}


def land(repo: Repo, args) -> dict:
    state = repo.load()
    spot = where(repo, ask=False)
    if state.get("phase") != "ready":
        raise Stop("stale", "run prepare first; nothing is ready to land")
    tip, base, start, branch = state.get("tip"), state.get("base"), state.get("start"), spot["branch"]
    if not (git("rev-parse", "HEAD") == tip == args.tip) or dirty():
        raise Stop("stale", "the worktree is not the reviewed tip; run prepare again and review the new packet")
    if not (isinstance(base, str) and isinstance(start, str) and ancestor(start, base) and ancestor(base, tip)):
        raise Stop("refused", "the saved base does not sit between the remote branch and the tip; run prepare again")
    title = f"Merge {branch}: {args.title}" if args.title else f"Merge {branch} into {spot['feature']}"
    # The tip is rebased onto the base, so the merge's tree is the tip's: build it without a checkout.
    merge = git("commit-tree", f"{tip}^{{tree}}", "-p", base, "-p", tip, "-m", title)
    target = f"refs/heads/{spot['upstream']}"
    # The lease makes the push land only on the remote commit the packet was built from.
    # Skipping the hook needs proof it refused this packet; the user's yes to skip is asked for after that.
    if args.no_verify and state.get("hook") != "pre-push":
        raise Stop("refused", "--no-verify needs a land of this packet that the pre-push hook refused")
    verify = ["--no-verify"] if args.no_verify else []
    pushed = run("push", "--porcelain", *verify, f"--force-with-lease={target}:{start}", END, spot["remote"],
                 f"{merge}:{target}", network=True)
    if pushed.returncode:
        refs = [line.split("\t") for line in pushed.stdout.splitlines() if line.startswith("!")]
        if any(len(ref) > 2 and ref[1].endswith(f":{target}") and ref[2].startswith("[rejected]") for ref in refs):
            repo.forget()
            raise Stop("rejected", f"{spot['remote']}/{spot['upstream']} moved since the packet; "
                                   "run prepare again and review the new packet")
        # A pre-push hook stops the push before git reports any ref; a remote refusal reports each ref.
        if not (args.no_verify or pushed.stdout.strip()) and os.access(git("rev-parse", "--git-path", "hooks/pre-push"), os.X_OK):
            repo.save(**state, hook="pre-push")
            raise Stop("refused", f"the pre-push hook refused the push: {why(pushed)}", hook="pre-push")
        raise Stop("refused", f"the push failed: {why(pushed)}")
    repo.forget()
    return {"status": "landed", "merge": merge, "feature": spot["feature"],
            "pushed": f"{spot['remote']}/{spot['upstream']}", "branch": branch}


def herdr(*args: str, timeout: int) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None


def herdr_workspace(main: str, path: str) -> str | None:
    """The Herdr workspace showing this worktree, when running inside Herdr."""
    if os.environ.get("HERDR_ENV") != "1":
        return None
    done = herdr("worktree", "list", "--cwd", main, timeout=10)
    try:
        listed = json.loads(done.stdout)["result"]["worktrees"] if done and done.returncode == 0 else []
    except (ValueError, KeyError, TypeError):
        return None
    for entry in listed if isinstance(listed, list) else []:
        if isinstance(entry, dict) and os.path.realpath(str(entry.get("path"))) == os.path.realpath(path):
            workspace = entry.get("open_workspace_id")
            return workspace if isinstance(workspace, str) and workspace else None
    return None


def cleanup(repo: Repo, _args) -> dict:
    spot = where(repo, ask=False)
    fetch(spot, spot["upstream"])
    if not ancestor("HEAD", spot["start"]):
        raise Stop("refused", f"{spot['branch']} is not in {spot['remote']}/{spot['upstream']} yet; land it first")
    files = dirty()
    if files:
        raise Stop("refused", "the worktree has files that removing it would lose", files=files)
    # Ignored files are rebuildable or copied in; they go with the worktree, and the result names them.
    ignored = [path for code, path in changed("--ignored=traditional") if code == "!!"]
    nested = nested_repos(repo.root, [path for path in ignored if path.endswith("/")])
    if nested:
        raise Stop("refused", "ignored folders hold repositories or worktrees that removing it would lose",
                   files=nested)
    dropped = {"dropped": ignored[:20], "dropped_count": len(ignored)}
    main, path, branch = spot["main"], repo.root, spot["branch"]
    workspace = herdr_workspace(main, path)
    if workspace:
        # Removing the workspace ends this agent's own pane, so a detached process finishes the job.
        log = os.path.join(repo.common_dir, FINISH_LOG)
        # finish reads its job from the repository, so a hand-run finish cannot name what it removes or writes.
        with open(os.path.join(repo.common_dir, FINISH_JOB), "w", encoding="utf-8") as handle:
            json.dump({"workspace": workspace, "branch": branch, "landed": spot["start"]}, handle)
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "finish", f"--main={main}"],
                         cwd=main, start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "removing", "method": "herdr", "workspace": workspace, "branch": branch,
                "path": path, "log": log, **dropped}
    git("worktree", "remove", END, path, cwd=main)
    git("branch", "-D", END, branch, cwd=main)
    return {"status": "removed", "method": "git", "branch": branch, "path": path, **dropped}


def finish(args) -> dict:
    """Close the workspace and delete the branch that cleanup queued in the main checkout's repository."""
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=args.main)
    try:
        with open(os.path.join(common, FINISH_JOB), encoding="utf-8") as handle:
            job = json.load(handle)
        os.remove(os.path.join(common, FINISH_JOB))
        workspace, branch, landed = job["workspace"], job["branch"], job["landed"]
    except (OSError, ValueError, KeyError, TypeError):
        raise Stop("refused", "no cleanup is waiting to finish here")
    removed = herdr("worktree", "remove", "--workspace", workspace, timeout=60)
    result = {"status": "refused", "herdr": why(removed) if removed else "herdr not found or timed out"}
    if removed and removed.returncode == 0:
        # A commit made after cleanup's check must not vanish with the branch.
        if run("merge-base", "--is-ancestor", END, f"refs/heads/{branch}", landed, cwd=args.main).returncode:
            result["branch"] = f"{branch} has commits that never landed, so it was kept"
        else:
            deleted = run("branch", "-D", END, branch, cwd=args.main)
            result.update(status="removed" if deleted.returncode == 0 else "refused", branch=why(deleted))
    # Written whole, then moved into place, so a reader never sees a half-written log.
    log = os.path.join(common, FINISH_LOG)
    with open(f"{log}.tmp", "w", encoding="utf-8") as handle:
        json.dump(result, handle)
    os.replace(f"{log}.tmp", log)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge a finished worktree into its remote feature branch.")
    parser.add_argument("--worktree", metavar="PATH", help="the worktree to act on; the current folder by default")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_cmd = commands.add_parser("prepare", help="build a fresh base, rebase, and print the packet's facts")
    prepare_cmd.add_argument("--parent", help="store the feature branch's parent branch, then prepare")
    resume_cmd = commands.add_parser("continue", help="conclude a resolved conflict and carry on")
    resume_cmd.add_argument("--clash", action="append", default=[], metavar="PATH: WHY",
                            help="one judgment call, recorded as a Clash-resolved trailer")
    commands.add_parser("abort", help="stop a prepare that hit a conflict, and go back to the branch")
    land_cmd = commands.add_parser("land", help="merge with --no-ff and push, after the review gate")
    land_cmd.add_argument("--tip", required=True, help="the `tip` from the packet")
    land_cmd.add_argument("--title", help="the merge commit's subject, after the branch name")
    land_cmd.add_argument("--no-verify", action="store_true", help="skip the pre-push hook, when the user approved it")
    commands.add_parser("cleanup", help="remove the worktree, its ignored files and its branch, once landed")
    finish_cmd = commands.add_parser("finish")
    finish_cmd.add_argument("--main", required=True)
    args = parser.parse_args()
    try:
        if args.command == "finish":
            result = finish(args)
        else:
            if args.worktree:
                os.chdir(args.worktree)
            handler = {"prepare": prepare, "continue": resume, "abort": abort, "land": land, "cleanup": cleanup}
            result = handler[args.command](Repo(), args)
    except Stop as stop:
        result = {"status": stop.status, "problem": stop.problem, **stop.facts}
    except (OSError, ValueError) as error:
        result = {"status": "refused", "problem": str(error)}
    print(json.dumps({"problem": None, "warnings": []} | result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
