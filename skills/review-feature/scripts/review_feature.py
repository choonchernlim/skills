#!/usr/bin/env python3
"""Prepare a feature branch for review, and publish the approved fixes.

Purpose: catch the feature checkout up with its remote, merge the remote
parent, and report the range merged since the last review, so reviewers read
every merged solution as one change; after the review gate, commit the staged
fixes, push them leased on the remote commit the review started from, and
move the review marker.
Usage: run in the feature checkout, on the feature branch.
  python3 review_feature.py start [--parent BRANCH]
  python3 review_feature.py continue [--clash "PATH: WHY"]...
  python3 review_feature.py abort
  python3 review_feature.py finish --head SHA --tree SHA [--message TEXT]
Output: one JSON object. `status` is one of refused, needs-parent, conflict,
ready, aborted, stale, rejected or pushed; with `problem`, and the facts each
status needs. Exit 0 unless the arguments are wrong. Needs git 2.32 or later.

The marker is `refs/reviewed/<branch>`, local to this clone. The parent branch
is `branch.<feature>.parent` in git config, which `start --parent` stores once.
Each commit this script makes carries a `Review-feature:` trailer, so a later
`start` can tell its unpushed commits from anyone else's.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys

STATE = "review-feature.json"
MARKER = "refs/reviewed/"
TRAILER = "Clash-resolved"
# Each path a conflict stopped on, so the review reads it even when the resolution took one side whole.
CONFLICTED = "Conflicted"
OWN = "Review-feature"
NETWORK = 120
MIN_GIT = (2, 32)
# Never prompt for credentials or messages: a prompt would hang an agent's shell.
QUIET = {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never", "GIT_EDITOR": "true"}
# Replay recorded resolutions, but never stage them: each one still waits for the agent's check.
RERERE = ("-c", "rerere.enabled=true", "-c", "rerere.autoUpdate=false")
END = "--end-of-options"
WORKTREE_BRANCH = re.compile(r"worktree-v\d+")
DOCS = re.compile(r"(^|/)(docs?/|README[^/]*$|CHANGELOG[^/]*$)|\.(md|mdx|rst|adoc)$", re.I)


class Stop(Exception):
    """Ends a command with a status other than success; `facts` join the output."""

    def __init__(self, status: str, problem: str | None = None, **facts):
        super().__init__(problem or status)
        self.status, self.problem, self.facts = status, problem, facts


def run(*args: str, network: bool = False) -> subprocess.CompletedProcess:
    """Run git in its own session, with no terminal to prompt on; a network call is killed whole on timeout."""
    process = subprocess.Popen(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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


def raw(*args: str, network: bool = False, failed: str | None = None) -> str:
    done = run(*args, network=network)
    if done.returncode:
        raise Stop("refused", f"{failed or 'git ' + ' '.join(args)} failed: {why(done)}")
    return done.stdout


def git(*args: str, network: bool = False, failed: str | None = None) -> str:
    return raw(*args, network=network, failed=failed).strip()


def lines(*args: str) -> list[str]:
    return git(*args).splitlines()


def paths(*args: str) -> list[str]:
    """The NUL-separated output of a `-z` command, so no path is quoted or split."""
    return [entry for entry in raw("--literal-pathspecs", *args).split("\0") if entry.strip("\n")]


def ancestor(older: str, newer: str) -> bool:
    return run("merge-base", "--is-ancestor", END, older, newer).returncode == 0


def safe_branch(name: str) -> bool:
    return not name.startswith("-") and run("check-ref-format", "--branch", name).returncode == 0


class Repo:
    """This checkout's git folder and the branch config, read once per command."""

    def __init__(self):
        found = re.search(r"(\d+)\.(\d+)", run("version").stdout)
        if not found or tuple(map(int, found.groups())) < MIN_GIT:
            raise Stop("refused", f"git {'.'.join(map(str, MIN_GIT))} or later is needed")
        self.git_dir = git("rev-parse", "--path-format=absolute", "--git-dir")
        listed = run("config", "-z", "--get-regexp", r"^branch\.").stdout
        self.config = dict(entry.split("\n", 1) for entry in listed.split("\0") if "\n" in entry)

    def path(self, name: str) -> str:
        return os.path.join(self.git_dir, name)

    def merging(self) -> bool:
        return os.path.exists(self.path("MERGE_HEAD"))

    def stopped(self) -> str | None:
        if self.merging():
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


def changed() -> list[tuple[str, str]]:
    """(XY, path) for each path `git status` reports, untracked ones included; a rename lists its new path once."""
    entries, found, source_next = run("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout.split("\0"), [], False
    for entry in entries:
        if source_next or not entry:
            source_next = False
            continue
        found.append((entry[:2], entry[3:]))
        source_next = entry[0] in "RC"
    return found


def unmerged() -> list[str]:
    return paths("diff", "--name-only", "-z", "--diff-filter=U")


def where(repo: Repo, ask: bool = True, parent: str | None = None) -> dict:
    """The feature branch, its remote and upstream, and its parent, or a Stop."""
    branch = run("symbolic-ref", "--short", "-q", "HEAD").stdout.strip()
    if not branch:
        raise Stop("refused", "HEAD is detached; switch to the feature branch first")
    if WORKTREE_BRANCH.fullmatch(branch):
        raise Stop("refused", f"{branch} is a worktree branch; run merge-worktree there, then review its feature branch")
    remote, merge = repo.config.get(f"branch.{branch}.remote"), repo.config.get(f"branch.{branch}.merge")
    if not remote or remote == "." or not merge:
        raise Stop("refused", f"{branch} has no upstream on a remote; push it with git push -u <remote> {branch}")
    upstream = merge.removeprefix("refs/heads/")
    if upstream != branch:
        # finish pushes to the upstream, so a branch tracking another one would publish there.
        raise Stop("refused", f"{branch} tracks {remote}/{upstream}, a branch of another name; "
                              f"track {remote}/{branch} with git branch -u {remote}/{branch}")
    if parent and (parent in (branch, upstream) or not safe_branch(parent)):
        raise Stop("refused", f"{parent!r} cannot be the parent of {branch}")
    parent = parent or repo.config.get(f"branch.{branch}.parent")
    if not parent and ask:
        default = run("symbolic-ref", "--short", "-q", f"refs/remotes/{remote}/HEAD").stdout.strip()
        raise Stop("needs-parent", f"{branch} has no parent branch recorded; ask which branch it merges from",
                   feature=branch, suggest=default.removeprefix(f"{remote}/") or None)
    return {"branch": branch, "remote": remote, "upstream": upstream, "parent": parent,
            "start": f"refs/remotes/{remote}/{upstream}", "parent_ref": f"refs/remotes/{remote}/{parent}"}


def fetch(spot: dict) -> None:
    """Fetch the upstream and the parent into their remote-tracking refs, whatever the remote's own refspec covers."""
    specs = [f"+refs/heads/{name}:refs/remotes/{spot['remote']}/{name}" for name in (spot["upstream"], spot["parent"])]
    git("fetch", "--quiet", "--no-tags", END, spot["remote"], *specs, network=True, failed=f"fetching {spot['remote']}")


def merge(repo: Repo, spot: dict, phase: str, ref: str, title: str) -> None:
    """Merge `ref` with --no-ff as a commit of this script's; on a conflict, save the phase and stop."""
    done = run(*RERERE, "merge", "--no-ff", "--no-log", "--no-edit", "-m", title, "-m", f"{OWN}: merge", END, ref)
    if not done.returncode:
        return
    files = unmerged()
    if not (repo.merging() and files):
        run("merge", "--abort")
        raise Stop("refused", f"merging {ref} failed: {why(done)}")
    repo.save(phase=phase, branch=spot["branch"], files=files)
    remaining = run(*RERERE, "rerere", "remaining").stdout.splitlines()
    raise Stop("conflict", None, phase=phase, files=files, replayed=[name for name in files if name not in remaining])


def catch_up(repo: Repo, spot: dict) -> dict:
    """Bring in the remote branch, then the remote parent, then report the range."""
    if not ancestor(spot["start"], "HEAD"):
        if ancestor("HEAD", spot["start"]):
            git("merge", "--ff-only", "--quiet", END, spot["start"])
        else:
            merge(repo, spot, "remote", spot["start"], f"Merge {spot['remote']}/{spot['upstream']} into {spot['branch']}")
    if not ancestor(spot["parent_ref"], "HEAD"):
        merge(repo, spot, "parent", spot["parent_ref"], f"Merge {spot['parent']} into {spot['branch']}")
    return ready(repo, spot)


def ready(repo: Repo, spot: dict) -> dict:
    head, start, parent = lines("rev-parse", "HEAD", spot["start"], spot["parent_ref"])
    marker = run("rev-parse", "-q", "--verify", f"{MARKER}{spot['branch']}^{{commit}}").stdout.strip()
    since = marker if marker and ancestor(marker, head) else None
    # The feature's own commits since the last review; the parent's history is the team's, not this review's.
    own = [f"{since}..{head}" if since else head, f"^{parent}"]
    # A merge lists the files it changed against every parent, so a resolution's own edits are reviewed too;
    # a rename counts as a deletion and an addition, so the old path's callers are reviewed.
    logged = paths("log", "-z", "--format=", "--name-only", "--no-renames", "--diff-merges=dense-combined", *own)
    conflicted = sorted({path.strip() for path in lines("log", f"--format=%(trailers:key={CONFLICTED},valueonly,unfold)", *own)
                         if path.strip()})
    files = sorted({path.strip("\n") for path in logged} | set(conflicted))
    status, counts = [], []
    if files:
        found = paths("diff", "-z", "--name-status", "--no-renames", parent, head, "--", *files)
        status = [f"{code}\t{path}" for code, path in zip(found[::2], found[1::2])]
        counts = [entry.split("\t", 2) for entry in paths("diff", "-z", "--numstat", "--no-renames", parent, head, "--", *files)]
    # Binary files count as "-"; a code file that lost lines may leave callers or dead code behind.
    numbers = [(int(add), int(cut), path) for add, cut, path in counts if add != "-"]
    repo.save(phase="ready", branch=spot["branch"], head=head, start=start)
    return {
        "status": "ready", "branch": spot["branch"], "parent": spot["parent"],
        "target": f"{spot['remote']}/{spot['upstream']}", "base": parent, "head": head, "marker": since,
        "commits": int(git("rev-list", "--count", *own)),
        "merges": lines("log", "--first-parent", "--merges", "--format=%s", *own),
        "files": status, "conflicted": conflicted,
        "added": sum(add for add, _, _ in numbers),
        "removed": sum(cut for _, cut, _ in numbers),
        "clashes": [note.strip() for note in
                    lines("log", f"--format=%(trailers:key={TRAILER},valueonly,unfold)", *own) if note.strip()],
        "reviewers": {
            "dead_code": any(cut and not DOCS.search(path) for _, cut, path in numbers),
            "docs": any(DOCS.search(path) for _, _, path in counts),
        },
        "unpushed": head != start,
    }


def start(repo: Repo, args) -> dict:
    stopped = repo.stopped()
    if stopped:
        ours = stopped == "merge" and repo.load().get("phase") in ("remote", "parent")
        hint = "resolve it and run continue, or run abort" if ours else "this skill did not start it; finish or abort it with git"
        raise Stop("refused", f"a {stopped} is stopped here; {hint}", files=unmerged())
    spot = where(repo, parent=args.parent)
    dirty = [path for _, path in changed()]
    if dirty:
        raise Stop("refused", "the checkout has uncommitted changes; commit, push or remove them first", files=dirty)
    fetch(spot)
    if args.parent:
        git("config", f"branch.{spot['branch']}.parent", args.parent)
    # Local commits outside the parent's history pass only when this script made them all.
    local = lines("log", f"--format=%(trailers:key={OWN},valueonly,separator=%x2C)%x00%h %s",
                  f"{spot['start']}..HEAD", f"^{spot['parent_ref']}")
    foreign = [line.split("\0", 1)[1] for line in local if line.startswith("\0")]
    if foreign:
        raise Stop("refused", "the branch has local commits that are not on its remote; push or remove them first",
                   files=foreign)
    return catch_up(repo, spot)


def resume(repo: Repo, args) -> dict:
    state = repo.load()
    if state.get("phase") not in ("remote", "parent") or not repo.merging():
        raise Stop("refused", "no conflict from start is open here; run start")
    spot = where(repo)
    if spot["branch"] != state.get("branch"):
        raise Stop("refused", f"the conflict belongs to {state.get('branch')}; switch back to it")
    files = unmerged()
    if files:
        raise Stop("refused", "some files are still unmerged; resolve them and git add each", files=files)
    loose = [path for code, path in changed() if code[1] not in " ?"]
    if loose:
        raise Stop("refused", "some resolved files are not staged; git add each", files=loose)
    check = run("diff", "--cached", "--check").stdout.splitlines()
    marked = sorted({line.split(":", 1)[0] for line in check if "leftover conflict marker" in line}
                    & set(state.get("files") or []))
    if marked:
        raise Stop("refused", "conflict markers are still in staged files", files=marked)
    clashes = [arg for clash in args.clash for arg in ("--trailer", f"{TRAILER}: {clash}")]
    clashes += [arg for path in state.get("files") or [] for arg in ("--trailer", f"{CONFLICTED}: {path}")]
    git(*RERERE, "commit", "-q", "--no-edit", "--cleanup=strip", *clashes)
    return catch_up(repo, spot)


def abort(repo: Repo, _args) -> dict:
    """Back out of a conflict from start; a merge this script already made stays, and the next start accepts it."""
    if repo.load().get("phase") not in ("remote", "parent") or not repo.merging():
        raise Stop("refused", "no conflict from start is open here; a merge or rebase of your own is yours to abort")
    run("merge", "--abort")
    repo.forget()
    return {"status": "aborted", "head": git("rev-parse", "HEAD")}


def finish(repo: Repo, args) -> dict:
    state = repo.load()
    spot = where(repo, ask=False)
    if state.get("phase") != "ready" or state.get("branch") != spot["branch"]:
        raise Stop("stale", "run start first; no review is ready to finish")
    head, start = state.get("head"), state.get("start")
    if not (git("rev-parse", "HEAD") == head == args.head):
        raise Stop("stale", "the branch is not the reviewed head; run start again and review the new range")
    if not (isinstance(start, str) and ancestor(start, head)):
        raise Stop("refused", "the saved start is not under the reviewed head; run start again")
    status = changed()
    loose = [path for code, path in status if code[1] != " "]
    if loose:
        raise Stop("refused", "stage the approved fixes only; these are not staged", files=loose)
    if git("write-tree") != args.tree:
        raise Stop("stale", "the staged fixes are not the approved ones; show gate ③ again with the staged diff")
    commit = None
    if status:
        if not args.message:
            raise Stop("refused", "staged fixes need a commit --message")
        git("commit", "-q", "-m", args.message, "--trailer", f"{OWN}: fixes")
        commit = head = git("rev-parse", "HEAD")
    target = f"refs/heads/{spot['upstream']}"
    # Saved first, so a push that times out can be retried on the new head.
    repo.save(phase="ready", branch=spot["branch"], head=head, start=start)
    retry = f"fix the cause, then finish --head {head} --tree {git('rev-parse', 'HEAD^{tree}')}"
    try:
        # The lease makes the push land only on the remote commit the review started from; tags and submodules stay.
        pushed = run("push", "--porcelain", "--no-follow-tags", "--no-recurse-submodules",
                     f"--force-with-lease={target}:{start}", END, spot["remote"], f"{head}:{target}", network=True)
    except Stop as stop:
        raise Stop("refused", f"{stop.problem}; {retry}", commit=commit) from None
    if pushed.returncode:
        refs = [line.split("\t") for line in pushed.stdout.splitlines() if line.startswith("!")]
        if any(len(ref) > 2 and ref[1].endswith(f":{target}") and ref[2].startswith("[rejected]") for ref in refs):
            repo.forget()
            raise Stop("rejected", f"{spot['remote']}/{spot['upstream']} moved during the review; "
                                   "run start again and review what arrived", commit=commit)
        raise Stop("refused", f"the push failed: {why(pushed)}; {retry}", commit=commit)
    git("update-ref", "-m", "review-feature", MARKER + spot["branch"], head)
    repo.forget()
    return {"status": "pushed", "commit": commit, "head": head, "pushed": f"{spot['remote']}/{spot['upstream']}",
            "marker": MARKER + spot["branch"]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a feature branch for review, and publish the approved fixes.")
    commands = parser.add_subparsers(dest="command", required=True)
    start_cmd = commands.add_parser("start", help="catch up, merge the remote parent, and report the range")
    start_cmd.add_argument("--parent", help="store the feature branch's parent branch, then start")
    resume_cmd = commands.add_parser("continue", help="conclude a resolved conflict and carry on")
    resume_cmd.add_argument("--clash", action="append", default=[], metavar="PATH: WHY",
                            help="one judgment call, recorded as a Clash-resolved trailer")
    commands.add_parser("abort", help="stop a start that hit a conflict")
    finish_cmd = commands.add_parser("finish", help="commit the staged fixes, push, and move the marker")
    finish_cmd.add_argument("--head", required=True, help="the `head` from the review the user approved")
    finish_cmd.add_argument("--tree", required=True, help="`git write-tree` of the staged fixes the user approved")
    finish_cmd.add_argument("--message", help="the fixes commit's message, when fixes are staged")
    args = parser.parse_args()
    handler = {"start": start, "continue": resume, "abort": abort, "finish": finish}[args.command]
    try:
        result = handler(Repo(), args)
    except Stop as stop:
        result = {"status": stop.status, "problem": stop.problem, **stop.facts}
    except (OSError, ValueError) as error:
        result = {"status": "refused", "problem": str(error)}
    print(json.dumps({"problem": None} | result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
