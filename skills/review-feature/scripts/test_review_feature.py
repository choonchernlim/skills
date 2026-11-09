#!/usr/bin/env python3
"""Self-test for review_feature.py.

Purpose: prove each review rule against throwaway repositories with a bare
remote and a teammate's clone, so a change cannot push unreviewed work, review
the wrong range, or lose a race silently.
Usage: python3 scripts/test_review_feature.py
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_feature.py")
# Drop inherited GIT_* variables, so no hook or caller steers the fixtures.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | {
    "GIT_CEILING_DIRECTORIES": os.path.realpath(tempfile.gettempdir()),
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True, env=ENV).stdout.strip()


def write(root: str, path: str, text: str, message: str | None = None) -> None:
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as handle:
        handle.write(text)
    if message:
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", message)


FOLDERS = ("origin.git", "main", "mate")
# Built once by main(); each case copies it, which is far cheaper than a dozen git calls per case.
TEMPLATE = ""


def build(base: str) -> None:
    """A bare remote on develop, a pushed feature/x checked out in main, and a teammate's clone."""
    remote, main, mate = (os.path.join(base, name) for name in FOLDERS)
    git(base, "init", "-q", "--bare", "-b", "develop", remote)
    git(base, "clone", "-q", remote, main)
    write(main, "shared.txt", "one\ntwo\nthree\n")
    write(main, "lib.py", "def keep():\n    return 1\n\n\ndef gone():\n    return 2\n", "start")
    git(main, "push", "-q", "origin", "develop")
    git(main, "remote", "set-head", "origin", "develop")
    git(main, "switch", "-q", "-c", "feature/x")
    git(main, "push", "-q", "-u", "origin", "feature/x")
    git(main, "config", "branch.feature/x.parent", "develop")
    git(base, "clone", "-q", remote, mate)


def world(base: str, parent: bool = True) -> dict:
    """A copy of the template, its clones pointed at the copied remote."""
    remote, main, mate = (os.path.join(base, name) for name in FOLDERS)
    for name in FOLDERS:
        shutil.copytree(os.path.join(TEMPLATE, name), os.path.join(base, name), symlinks=True)
    for clone in (main, mate):
        git(clone, "remote", "set-url", "origin", remote)
    if not parent:
        git(main, "config", "--unset", "branch.feature/x.parent")
    return {"base": base, "remote": remote, "main": main, "mate": mate}


def mate_push(places: dict, branch: str, path: str, text: str) -> None:
    mate = places["mate"]
    git(mate, "fetch", "-q", "origin")
    git(mate, "switch", "-q", "-C", branch, f"origin/{branch}")
    write(mate, path, text, f"mate edits {path} on {branch}")
    git(mate, "push", "-q", "origin", branch)


def land(places: dict, version: int, path: str | None = None, text: str = "a\nb\n") -> None:
    """Land worktree vN on the remote feature branch with --no-ff, as merge-worktree does."""
    mate = places["mate"]
    git(mate, "fetch", "-q", "origin")
    git(mate, "switch", "-q", "-C", "feature/x", "origin/feature/x")
    git(mate, "switch", "-q", "-c", f"worktree-v{version}")
    write(mate, path or f"app{version}.txt", text, f"build v{version}")
    git(mate, "switch", "-q", "feature/x")
    git(mate, "merge", "-q", "--no-ff", "-m", f"Merge worktree-v{version}: demo {version}", f"worktree-v{version}")
    git(mate, "push", "-q", "origin", "feature/x")


def run(cwd: str, *args: str) -> dict:
    done = subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd, capture_output=True, text=True, env=ENV)
    if done.returncode:
        raise AssertionError(f"exit {done.returncode}: {done.stderr.strip()}")
    return json.loads(done.stdout)


def hook(folder: str, name: str, body: str = "exit 1") -> None:
    path = os.path.join(folder, "hooks", name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"#!/bin/sh\n{body}\n")
    os.chmod(path, 0o755)


def remote_head(places: dict) -> str:
    return git(places["remote"], "rev-parse", "feature/x")


def state_path(places: dict) -> str:
    return os.path.join(places["main"], ".git", "review-feature.json")


def state(places: dict) -> dict:
    if not os.path.exists(state_path(places)):
        return {}
    with open(state_path(places), encoding="utf-8") as handle:
        return json.load(handle)


def save_state(places: dict, saved: dict) -> None:
    with open(state_path(places), "w", encoding="utf-8") as handle:
        json.dump(saved, handle)


def parent_stored(places: dict) -> bool:
    return subprocess.run(["git", "-C", places["main"], "config", "branch.feature/x.parent"],
                          capture_output=True, env=ENV).returncode == 0


def parent_conflict(places: dict) -> dict:
    """The feature and develop both change line two of shared.txt."""
    land(places, 1, "shared.txt", "one\ntwo-feature\nthree\n")
    mate_push(places, "develop", "shared.txt", "one\ntwo-develop\nthree\n")
    return run(places["main"], "start")


def remote_conflict(places: dict) -> dict:
    """start leaves its develop merge unpushed, then the teammate changes the same line on the feature branch."""
    mate_push(places, "develop", "shared.txt", "one\ntwo-develop\nthree\n")
    first = run(places["main"], "start")
    assert first["status"] == "ready" and first["unpushed"], first
    mate_push(places, "feature/x", "shared.txt", "one\ntwo-mate\nthree\n")
    return run(places["main"], "start")


def resolve(places: dict, text: str = "one\ntwo-both\nthree\n") -> None:
    write(places["main"], "shared.txt", text)
    git(places["main"], "add", "shared.txt")


def finish(places: dict, head: str, *extra: str) -> dict:
    """finish, approving whatever is staged now."""
    return run(places["main"], "finish", "--head", head, "--tree", git(places["main"], "write-tree"), *extra)


def fix(places: dict, got: dict, message: str = "Fix review findings") -> dict:
    write(places["main"], "app1.txt", "a\nb fixed\n")
    git(places["main"], "add", "app1.txt")
    return finish(places, got["head"], "--message", message)


def detached_head_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "switch", "-q", "--detach")
    got = run(places["main"], "start")
    return [got["status"], "detached" in got["problem"]], ["refused", True]


def worktree_branch_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "switch", "-q", "-c", "worktree-v3")
    got = run(places["main"], "start")
    return [got["status"], "merge-worktree" in got["problem"]], ["refused", True]


def unpushed_feature_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "switch", "-q", "-c", "feature/y")
    got = run(places["main"], "start")
    return [got["status"], "no upstream" in got["problem"]], ["refused", True]


def upstream_of_another_name_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "switch", "-q", "-c", "feature/y", "--track", "origin/develop")
    got = run(places["main"], "start")
    return [got["status"], "another name" in got["problem"]], ["refused", True]


def local_upstream_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "switch", "-q", "-c", "feature/y", "--track", "develop")
    got = run(places["main"], "start")
    return [got["status"], "no upstream" in got["problem"]], ["refused", True]


def uncommitted_work_is_listed(base: str) -> tuple:
    places = world(base)
    write(places["main"], "shared.txt", "edited\n")
    write(places["main"], "notes/new.txt", "new\n")
    got = run(places["main"], "start")
    return [got["status"], got["files"]], ["refused", ["shared.txt", "notes/new.txt"]]


def renamed_work_is_listed_once(base: str) -> tuple:
    places = world(base)
    git(places["main"], "mv", "shared.txt", "moved.txt")
    got = run(places["main"], "start")
    return [got["status"], got["files"]], ["refused", ["moved.txt"]]


def parent_is_asked_once(base: str) -> tuple:
    places = world(base, parent=False)
    asked = run(places["main"], "start")
    stored = run(places["main"], "start", "--parent", "develop")
    again = run(places["main"], "start")
    return ([asked["status"], asked["suggest"], stored["status"], again["status"],
             git(places["main"], "config", "branch.feature/x.parent")],
            ["needs-parent", "develop", "ready", "ready", "develop"])


def parent_cannot_be_the_feature(base: str) -> tuple:
    places = world(base, parent=False)
    got = run(places["main"], "start", "--parent", "feature/x")
    return [got["status"], "cannot be the parent" in got["problem"]], ["refused", True]


def unsafe_parent_is_never_stored(base: str) -> tuple:
    places = world(base, parent=False)
    got = run(places["main"], "start", "--parent", "bad..name")
    stored = parent_stored(places)
    return [got["status"], "cannot be the parent" in got["problem"], stored], ["refused", True, False]


def missing_parent_is_never_stored(base: str) -> tuple:
    places = world(base, parent=False)
    got = run(places["main"], "start", "--parent", "nowhere")
    stored = parent_stored(places)
    return [got["status"], got["problem"].startswith("fetching origin failed"), stored], ["refused", True, False]


def two_merged_worktrees_are_one_range(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    land(places, 2)
    got = run(places["main"], "start")
    return ([got["status"], got["commits"], got["merges"], got["files"], got["added"], got["removed"],
             got["head"] == remote_head(places), got["unpushed"], got["marker"], got["target"]],
            ["ready", 4, ["Merge worktree-v2: demo 2", "Merge worktree-v1: demo 1"],
             ["A\tapp1.txt", "A\tapp2.txt"], 4, 0, True, False, None, "origin/feature/x"])


def merges_inside_a_worktree_stay_out(base: str) -> tuple:
    places = world(base)
    mate = places["mate"]
    git(mate, "switch", "-q", "-C", "feature/x", "origin/feature/x")
    git(mate, "switch", "-q", "-c", "worktree-v1")
    git(mate, "switch", "-q", "-c", "side")
    write(mate, "side.txt", "side\n", "side work")
    git(mate, "switch", "-q", "worktree-v1")
    write(mate, "app1.txt", "a\n", "build v1")
    git(mate, "merge", "-q", "--no-ff", "-m", "Merge side into worktree", "side")
    git(mate, "switch", "-q", "feature/x")
    git(mate, "merge", "-q", "--no-ff", "-m", "Merge worktree-v1: demo 1", "worktree-v1")
    git(mate, "push", "-q", "origin", "feature/x")
    got = run(places["main"], "start")
    return got["merges"], ["Merge worktree-v1: demo 1"]


def edits_inside_a_merge_are_reviewed(base: str) -> tuple:
    places = world(base)
    mate = places["mate"]
    git(mate, "switch", "-q", "-C", "feature/x", "origin/feature/x")
    git(mate, "switch", "-q", "-c", "worktree-v1")
    write(mate, "app1.txt", "a\n", "build v1")
    git(mate, "switch", "-q", "feature/x")
    git(mate, "merge", "-q", "--no-ff", "--no-commit", "worktree-v1")
    write(mate, "shared.txt", "one\nslipped in\nthree\n")
    git(mate, "add", "shared.txt")
    git(mate, "commit", "-q", "-m", "Merge worktree-v1: demo 1")
    git(mate, "push", "-q", "origin", "feature/x")
    got = run(places["main"], "start")
    return got["files"], ["A\tapp1.txt", "M\tshared.txt"]


def parent_changes_are_merged_but_not_reviewed(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    mate_push(places, "develop", "team.txt", "team\n")
    got = run(places["main"], "start")
    subjects = git(places["main"], "log", "-1", "--format=%s")
    return ([got["status"], got["files"], got["unpushed"], subjects, got["base"] == git(places["remote"], "rev-parse", "develop")],
            ["ready", ["A\tapp1.txt"], True, "Merge develop into feature/x", True])


def parent_is_merged_even_when_it_could_fast_forward(base: str) -> tuple:
    places = world(base)
    mate_push(places, "develop", "team.txt", "team\n")
    got = run(places["main"], "start")
    return ([got["status"], git(places["main"], "log", "-1", "--format=%s"), got["files"]],
            ["ready", "Merge develop into feature/x", []])


def failed_parent_merge_is_undone(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    mate_push(places, "develop", "team.txt", "team\n")
    hook(os.path.join(places["main"], ".git"), "pre-merge-commit")
    got = run(places["main"], "start")
    return ([got["status"], os.path.exists(os.path.join(places["main"], ".git", "MERGE_HEAD")),
             git(places["main"], "status", "--porcelain")], ["refused", False, ""])


def parent_history_notes_stay_out(base: str) -> tuple:
    places = world(base)
    mate = places["mate"]
    git(mate, "switch", "-q", "develop")
    write(mate, "team.txt", "team\n")
    git(mate, "add", "team.txt")
    git(mate, "commit", "-q", "-m", "team work", "--trailer", "Clash-resolved: team.txt: not ours")
    git(mate, "push", "-q", "origin", "develop")
    land(places, 1)
    got = run(places["main"], "start")
    return [got["status"], got["clashes"]], ["ready", []]


def parent_conflict_resolves_with_a_trailer(base: str) -> tuple:
    places = world(base)
    stopped = parent_conflict(places)
    resolve(places)
    got = run(places["main"], "continue", "--clash", "shared.txt: kept both lines")
    message = git(places["main"], "log", "-1", "--format=%B")
    return ([stopped["status"], stopped["phase"], stopped["files"], got["status"], got["clashes"], got["unpushed"], message],
            ["conflict", "parent", ["shared.txt"], "ready", ["shared.txt: kept both lines"], True,
             "Merge develop into feature/x\n\nReview-feature: merge\nClash-resolved: shared.txt: kept both lines\n"
             "Conflicted: shared.txt"])


def replayed_resolution_still_stops_for_review(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "rerere.autoUpdate", "true")
    parent_conflict(places)
    resolve(places)
    run(places["main"], "continue")
    git(places["main"], "reset", "-q", "--hard", "HEAD^1")
    os.remove(state_path(places))
    got = run(places["main"], "start")
    return [got["status"], got["replayed"]], ["conflict", ["shared.txt"]]


def remote_conflict_follows_its_own_merge(base: str) -> tuple:
    places = world(base)
    stopped = remote_conflict(places)
    resolve(places)
    got = run(places["main"], "continue")
    return ([stopped["status"], stopped["phase"], got["status"], got["unpushed"],
             ancestor(places, remote_head(places), "HEAD")],
            ["conflict", "remote", "ready", True, True])


def ancestor(places: dict, older: str, newer: str) -> bool:
    return subprocess.run(["git", "-C", places["main"], "merge-base", "--is-ancestor", older, newer], env=ENV).returncode == 0


def continue_refuses_unmerged_files(base: str) -> tuple:
    places = world(base)
    parent_conflict(places)
    got = run(places["main"], "continue")
    return [got["status"], got["files"], "still unmerged" in got["problem"]], ["refused", ["shared.txt"], True]


def continue_needs_staged_files(base: str) -> tuple:
    places = world(base)
    parent_conflict(places)
    resolve(places)
    write(places["main"], "shared.txt", "one\nchanged again\nthree\n")
    got = run(places["main"], "continue")
    return [got["status"], got["files"]], ["refused", ["shared.txt"]]


def continue_refuses_conflict_markers(base: str) -> tuple:
    places = world(base)
    parent_conflict(places)
    git(places["main"], "add", "shared.txt")
    got = run(places["main"], "continue")
    return [got["status"], got["files"]], ["refused", ["shared.txt"]]


def heading_rule_is_not_a_marker(base: str) -> tuple:
    places = world(base)
    # The parent's new guide arrives staged in the merge, and git's check reads its rule as a marker.
    mate_push(places, "develop", "guide.md", "Title\n=======\n")
    parent_conflict(places)
    resolve(places)
    got = run(places["main"], "continue")
    return got["status"], "ready"


def continue_needs_the_conflicted_branch(base: str) -> tuple:
    places = world(base)
    parent_conflict(places)
    resolve(places)
    save_state(places, {"phase": "parent", "branch": "feature/other", "files": ["shared.txt"]})
    got = run(places["main"], "continue")
    return [got["status"], "belongs to feature/other" in got["problem"]], ["refused", True]


def continue_needs_an_open_conflict(base: str) -> tuple:
    places = world(base)
    run(places["main"], "start")
    got = run(places["main"], "continue")
    return [got["status"], "no conflict" in got["problem"]], ["refused", True]


def start_refuses_an_open_conflict(base: str) -> tuple:
    places = world(base)
    parent_conflict(places)
    got = run(places["main"], "start")
    return [got["status"], "stopped here" in got["problem"]], ["refused", True]


def abort_forgets_a_clean_start(base: str) -> tuple:
    places = world(base)
    parent_conflict(places)
    got = run(places["main"], "abort")
    return ([got["status"], got["head"] == remote_head(places), state(places), git(places["main"], "status", "--porcelain")],
            ["aborted", True, {}, ""])


def abort_leaves_other_merges_alone(base: str) -> tuple:
    places = world(base)
    land(places, 1, "shared.txt", "one\ntwo-feature\nthree\n")
    git(places["main"], "pull", "-q", "--ff-only")
    mate_push(places, "develop", "shared.txt", "one\ntwo-develop\nthree\n")
    git(places["main"], "fetch", "-q", "origin")
    subprocess.run(["git", "-C", places["main"], "merge", "origin/develop"], capture_output=True, env=ENV)
    started = run(places["main"], "start")
    got = run(places["main"], "abort")
    return ([started["status"], "did not start it" in started["problem"], got["status"],
             os.path.exists(os.path.join(places["main"], ".git", "MERGE_HEAD"))], ["refused", True, "refused", True])


def merge_log_config_keeps_the_trailer(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "merge.log", "true")
    mate_push(places, "develop", "team.txt", "team\n")
    first = run(places["main"], "start")
    again = run(places["main"], "start")
    return [first["status"], first["unpushed"], again["status"]], ["ready", True, "ready"]


def odd_paths_are_reviewed(base: str) -> tuple:
    places = world(base)
    land(places, 1, "notes/caf\u00e9 [draft].txt", "a\n")
    got = run(places["main"], "start")
    return got["files"], ["A\tnotes/caf\u00e9 [draft].txt"]


def renames_list_both_paths(base: str) -> tuple:
    places = world(base)
    mate = places["mate"]
    git(mate, "switch", "-q", "-C", "feature/x", "origin/feature/x")
    git(mate, "mv", "lib.py", "core.py")
    git(mate, "commit", "-q", "-m", "rename lib")
    git(mate, "push", "-q", "origin", "feature/x")
    got = run(places["main"], "start")
    return [got["files"], got["reviewers"]["dead_code"]], [["A\tcore.py", "D\tlib.py"], True]


def resolution_taking_one_side_is_reviewed(base: str) -> tuple:
    places = world(base)
    land(places, 1, "shared.txt", "one\ntwo-feature\nthree\n")
    fix(places, run(places["main"], "start"))
    mate_push(places, "develop", "shared.txt", "one\ntwo-develop\nthree\n")
    run(places["main"], "start")
    resolve(places, "one\ntwo-develop\nthree\n")
    got = run(places["main"], "continue")
    return [got["status"], got["files"], got["conflicted"]], ["ready", [], ["shared.txt"]]


def abort_keeps_its_own_merge(base: str) -> tuple:
    places = world(base)
    remote_conflict(places)
    run(places["main"], "abort")
    again = run(places["main"], "start")
    return [again["status"], again["phase"]], ["conflict", "remote"]


def local_commits_are_refused(base: str) -> tuple:
    places = world(base)
    write(places["main"], "mine.txt", "mine\n", "my own commit")
    got = run(places["main"], "start")
    return [got["status"], got["files"][0].endswith("my own commit")], ["refused", True]


def commits_after_start_are_refused(base: str) -> tuple:
    places = world(base)
    mate_push(places, "develop", "team.txt", "team\n")
    run(places["main"], "start")
    write(places["main"], "mine.txt", "mine\n", "my own commit")
    got = run(places["main"], "start")
    return got["status"], "refused"


def finish_commits_pushes_and_moves_the_marker(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    got = fix(places, run(places["main"], "start"))
    head = git(places["main"], "rev-parse", "HEAD")
    return ([got["status"], got["commit"] == head, remote_head(places) == head,
             git(places["main"], "rev-parse", "refs/reviewed/feature/x") == head,
             git(places["main"], "log", "-1", "--format=%s"), state(places)],
            ["pushed", True, True, True, "Fix review findings", {}])


def second_review_starts_at_the_marker(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    first = fix(places, run(places["main"], "start"))
    land(places, 2)
    got = run(places["main"], "start")
    return ([got["status"], got["marker"] == first["head"], got["files"], got["merges"], got["commits"]],
            ["ready", True, ["A\tapp2.txt"], ["Merge worktree-v2: demo 2"], 2])


def unrelated_marker_is_ignored(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    tree = git(places["main"], "rev-parse", "HEAD^{tree}")
    orphan = git(places["main"], "commit-tree", tree, "-m", "elsewhere")
    git(places["main"], "update-ref", "refs/reviewed/feature/x", orphan)
    got = run(places["main"], "start")
    return [got["status"], got["marker"], got["files"]], ["ready", None, ["A\tapp1.txt"]]


def finish_without_fixes_pushes_the_merge(base: str) -> tuple:
    places = world(base)
    mate_push(places, "develop", "team.txt", "team\n")
    ready = run(places["main"], "start")
    got = finish(places, ready["head"])
    return [got["status"], got["commit"], remote_head(places) == ready["head"]], ["pushed", None, True]


def finish_needs_a_start(base: str) -> tuple:
    places = world(base)
    got = finish(places, git(places["main"], "rev-parse", "HEAD"))
    return [got["status"], "run start first" in got["problem"]], ["stale", True]


def finish_needs_the_reviewed_head(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    got = finish(places, git(places["main"], "rev-parse", "HEAD~1"))
    return [got["status"], remote_head(places) == ready["head"]], ["stale", True]


def finish_after_a_new_commit_is_stale(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    write(places["main"], "extra.txt", "x\n", "unreviewed")
    got = finish(places, ready["head"])
    return [got["status"], remote_head(places) == ready["head"]], ["stale", True]


def tampered_start_is_refused(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    saved = state(places) | {"start": git(places["main"], "commit-tree", "HEAD^{tree}", "-m", "elsewhere")}
    save_state(places, saved)
    got = finish(places, ready["head"])
    return got["status"], "refused"


def finish_refuses_unstaged_and_untracked_files(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    write(places["main"], "app1.txt", "loose\n")
    write(places["main"], "scratch/new.txt", "new\n")
    got = finish(places, ready["head"], "--message", "Fix")
    return [got["status"], got["files"], remote_head(places) == ready["head"]], ["refused", ["app1.txt", "scratch/new.txt"], True]


def fixes_staged_after_approval_are_stale(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    write(places["main"], "app1.txt", "approved\n")
    git(places["main"], "add", "app1.txt")
    approved = git(places["main"], "write-tree")
    write(places["main"], "app1.txt", "slipped in later\n")
    git(places["main"], "add", "app1.txt")
    got = run(places["main"], "finish", "--head", ready["head"], "--tree", approved, "--message", "Fix")
    return [got["status"], remote_head(places) == ready["head"]], ["stale", True]


def finish_needs_a_message_for_fixes(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    write(places["main"], "app1.txt", "fixed\n")
    git(places["main"], "add", "app1.txt")
    got = finish(places, ready["head"])
    return [got["status"], "--message" in got["problem"]], ["refused", True]


def rejected_push_is_reviewed_again(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    land(places, 2)
    rejected = fix(places, ready)
    # The review is over once the remote moved: finish waits for a new start.
    retried = finish(places, rejected["commit"])
    again = run(places["main"], "start")
    done = finish(places, again["head"])
    return ([rejected["status"], bool(rejected["commit"]), retried["status"], again["status"],
             "A\tapp2.txt" in again["files"], done["status"], remote_head(places) == again["head"]],
            ["rejected", True, "stale", "ready", True, "pushed", True])


def failed_push_can_be_retried(base: str) -> tuple:
    places = world(base)
    land(places, 1)
    ready = run(places["main"], "start")
    hook(places["remote"], "pre-receive")
    failed = fix(places, ready)
    os.remove(os.path.join(places["remote"], "hooks", "pre-receive"))
    got = finish(places, failed["commit"])
    return ([failed["status"], got["status"], remote_head(places) == failed["commit"]],
            ["refused", "pushed", True])


def failed_fetch_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "remote", "set-url", "origin", os.path.join(base, "missing.git"))
    got = run(places["main"], "start")
    return [got["status"], got["problem"].startswith("fetching origin failed")], ["refused", True]


def narrow_fetch_config_still_sees_the_remote(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")
    land(places, 1)
    got = run(places["main"], "start")
    return [got["status"], got["files"]], ["ready", ["A\tapp1.txt"]]


def reviewers_join_by_trigger(base: str) -> tuple:
    plain, docs, removed, deleted = (os.path.join(base, name) for name in ("plain", "docs", "removed", "deleted"))
    found = []
    for folder, path, text in ((plain, "app1.txt", "a\n"), (docs, "README.md", "# Demo\n"),
                               (removed, "lib.py", "def keep():\n    return 1\n"), (deleted, None, None)):
        os.makedirs(folder)
        places = world(folder)
        if path:
            land(places, 1, path, text)
        else:
            mate = places["mate"]
            git(mate, "switch", "-q", "-C", "feature/x", "origin/feature/x")
            # A deleted file with no definitions in it still calls the dead-code reviewer.
            git(mate, "rm", "-q", "shared.txt")
            git(mate, "commit", "-q", "-m", "drop shared")
            git(mate, "push", "-q", "origin", "feature/x")
        reviewers = run(places["main"], "start")["reviewers"]
        found.append([reviewers["dead_code"], reviewers["docs"]])
    return found, [[False, False], [False, True], [True, False], [True, False]]


CASES = [
    detached_head_is_refused,
    worktree_branch_is_refused,
    unpushed_feature_is_refused,
    local_upstream_is_refused,
    upstream_of_another_name_is_refused,
    uncommitted_work_is_listed,
    renamed_work_is_listed_once,
    parent_is_asked_once,
    parent_cannot_be_the_feature,
    unsafe_parent_is_never_stored,
    missing_parent_is_never_stored,
    two_merged_worktrees_are_one_range,
    merges_inside_a_worktree_stay_out,
    edits_inside_a_merge_are_reviewed,
    parent_changes_are_merged_but_not_reviewed,
    parent_is_merged_even_when_it_could_fast_forward,
    failed_parent_merge_is_undone,
    parent_history_notes_stay_out,
    parent_conflict_resolves_with_a_trailer,
    replayed_resolution_still_stops_for_review,
    remote_conflict_follows_its_own_merge,
    continue_refuses_unmerged_files,
    continue_needs_staged_files,
    continue_refuses_conflict_markers,
    heading_rule_is_not_a_marker,
    continue_needs_the_conflicted_branch,
    continue_needs_an_open_conflict,
    start_refuses_an_open_conflict,
    abort_forgets_a_clean_start,
    abort_keeps_its_own_merge,
    abort_leaves_other_merges_alone,
    merge_log_config_keeps_the_trailer,
    odd_paths_are_reviewed,
    renames_list_both_paths,
    resolution_taking_one_side_is_reviewed,
    local_commits_are_refused,
    commits_after_start_are_refused,
    finish_commits_pushes_and_moves_the_marker,
    second_review_starts_at_the_marker,
    unrelated_marker_is_ignored,
    finish_without_fixes_pushes_the_merge,
    finish_needs_a_start,
    finish_needs_the_reviewed_head,
    finish_after_a_new_commit_is_stale,
    tampered_start_is_refused,
    finish_refuses_unstaged_and_untracked_files,
    fixes_staged_after_approval_are_stale,
    finish_needs_a_message_for_fixes,
    rejected_push_is_reviewed_again,
    failed_push_can_be_retried,
    failed_fetch_is_refused,
    narrow_fetch_config_still_sees_the_remote,
    reviewers_join_by_trigger,
]


def check(case) -> str | None:
    """Run one case in its own temporary folder; the failure text, or None when it holds."""
    with tempfile.TemporaryDirectory() as base:
        try:
            got, want = case(os.path.realpath(base))
        except (AssertionError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
            return f"{case.__name__}: {error}"
    return None if got == want else f"{case.__name__}: got {got!r}, want {want!r}"


def main() -> int:
    global TEMPLATE
    with tempfile.TemporaryDirectory() as template:
        TEMPLATE = os.path.realpath(template)
        build(TEMPLATE)
        # Cases share nothing, so they run side by side; the wait is on git processes, not Python.
        with concurrent.futures.ThreadPoolExecutor() as pool:
            failures = [f for f in pool.map(check, CASES) if f]
    if failures:
        print("\n\n".join(failures))
        print(f"\n{len(failures)} failure(s)")
        return 1
    print(f"ok: {len(CASES)} review rules hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
