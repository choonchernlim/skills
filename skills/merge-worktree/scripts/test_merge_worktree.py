#!/usr/bin/env python3
"""Self-test for merge_worktree.py.

Purpose: prove each merge rule against throwaway repositories with a bare
remote and a teammate's clone, so a change cannot push unreviewed work, lose a
race silently, or remove a worktree that has not landed.
Usage: python3 scripts/test_merge_worktree.py
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge_worktree.py")
# Drop inherited GIT_* and HERDR_* variables, so neither a hook nor a Herdr pane steers the fixtures.
ENV = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "HERDR_"))} | {
    "GIT_CEILING_DIRECTORIES": os.path.realpath(tempfile.gettempdir()),
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}
# A stand-in for herdr: lists the worktree in workspace w7, and removes it as Herdr would.
FAKE_HERDR = f"""#!{sys.executable}
import json, os, subprocess, sys
args = sys.argv[1:]
with open(os.environ["FAKE_HERDR_LOG"], "a") as log:
    log.write(" ".join(args) + "\\n")
if args[:2] == ["worktree", "list"]:
    print(json.dumps({{"result": {{"worktrees": [{{"path": os.environ["FAKE_WORKTREE"], "open_workspace_id": "w7"}}]}}}}))
elif args[:2] == ["worktree", "remove"]:
    if os.environ.get("FAKE_HERDR_MODE") == "fail":
        sys.exit("remove failed")
    subprocess.run(["git", "-C", os.environ["FAKE_MAIN"], "worktree", "remove", os.environ["FAKE_WORKTREE"]], check=True)
"""


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


def world(base: str) -> dict:
    """A bare remote on develop, a pushed feature/x, a teammate's clone, and worktree v1 on feature/x."""
    remote, main, mate = (os.path.join(base, name) for name in ("origin.git", "main", "mate"))
    git(base, "init", "-q", "--bare", "-b", "develop", remote)
    git(base, "clone", "-q", remote, main)
    write(main, "shared.txt", "one\ntwo\nthree\n", "start")
    git(main, "push", "-q", "origin", "develop")
    git(main, "remote", "set-head", "origin", "develop")
    git(main, "switch", "-q", "-c", "feature/x")
    git(main, "push", "-q", "-u", "origin", "feature/x")
    with open(os.path.join(main, ".git", "info", "exclude"), "a", encoding="utf-8") as handle:
        handle.write(".claude/worktrees/\n")
    git(main, "config", "branch.feature/x.parent", "develop")
    git(base, "clone", "-q", remote, mate)
    places = {"base": base, "remote": remote, "main": main, "mate": mate}
    places["v1"] = add_worktree(places, 1)
    return places


def add_worktree(places: dict, version: int) -> str:
    path = os.path.join(places["main"], ".claude", "worktrees", f"v{version}")
    git(places["main"], "worktree", "add", "-q", "-b", f"worktree-v{version}", path, "feature/x")
    git(places["main"], "config", f"branch.worktree-v{version}.parent", "feature/x")
    write(path, f"specs/v00{version}-demo/spec.md", "# Spec\n")
    write(path, f"specs/v00{version}-demo/plan.md", "# Plan\n\n- [x] Build\n- [x] Check\n- [ ] Polish\n")
    write(path, f"app{version}.txt", "a\nb\nc\n", f"build v{version}")
    return path


def mate_push(places: dict, branch: str, path: str, text: str) -> None:
    mate = places["mate"]
    git(mate, "fetch", "-q", "origin")
    git(mate, "switch", "-q", "-C", branch, f"origin/{branch}")
    write(mate, path, text, f"mate edits {path} on {branch}")
    git(mate, "push", "-q", "origin", branch)


def run(cwd: str, *args: str, env: dict | None = None) -> dict:
    done = subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd, capture_output=True, text=True, env=env or ENV)
    if done.returncode:
        raise AssertionError(f"exit {done.returncode}: {done.stderr.strip()}")
    return json.loads(done.stdout)


def rebase_conflict(places: dict) -> dict:
    """The teammate adds app1.txt on the feature branch, so rebasing v1 stops on it."""
    mate_push(places, "feature/x", "app1.txt", "a\nB-feature\nc\n")
    return run(places["v1"], "prepare")


def landed(places: dict, path: str | None = None) -> dict:
    ready = run(path or places["v1"], "prepare")
    return run(path or places["v1"], "land", "--tip", ready["tip"])


def hook(folder: str, name: str, body: str = "exit 1") -> None:
    path = os.path.join(folder, "hooks", name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"#!/bin/sh\n{body}\n")
    os.chmod(path, 0o755)


def remote_head(places: dict) -> str:
    return git(places["remote"], "rev-parse", "feature/x")


def main_checkout_is_refused(base: str) -> tuple:
    got = run(world(base)["main"], "prepare")
    return [got["status"], "main checkout" in got["problem"]], ["refused", True]


def detached_head_is_refused(base: str) -> tuple:
    v1 = world(base)["v1"]
    git(v1, "switch", "-q", "--detach")
    got = run(v1, "prepare")
    return [got["status"], "detached" in got["problem"]], ["refused", True]


def uncommitted_work_is_listed(base: str) -> tuple:
    v1 = world(base)["v1"]
    write(v1, "notes.txt", "draft\n")
    got = run(v1, "prepare")
    return [got["status"], got["files"]], ["refused", ["notes.txt"]]


def unpushed_feature_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "--unset", "branch.feature/x.remote")
    got = run(places["v1"], "prepare")
    return [got["status"], "no upstream" in got["problem"]], ["refused", True]


def parent_is_asked_once(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "--unset", "branch.feature/x.parent")
    asked = run(places["v1"], "prepare")
    stored = run(places["v1"], "prepare", "--parent", "develop")
    return ([asked["status"], asked["suggest"], stored["status"], git(places["main"], "config", "branch.feature/x.parent")],
            ["needs-parent", "develop", "ready", "develop"])


def packet_reports_the_work(base: str) -> tuple:
    places = world(base)
    got = run(places["v1"], "prepare")
    return ([got["status"], got["commits"], got["added"], got["removed"], got["files"], got["parent_commits"],
             got["pair"], got["base"] == remote_head(places)],
            ["ready", 1, 9, 0, ["A\tapp1.txt", "A\tspecs/v001-demo/plan.md", "A\tspecs/v001-demo/spec.md"], 0,
             {"folder": "specs/v001-demo", "open_steps": 1}, True])


def plan_without_spec_is_not_a_pair(base: str) -> tuple:
    places = world(base)
    git(places["v1"], "rm", "-q", "specs/v001-demo/spec.md")
    git(places["v1"], "commit", "-q", "-m", "drop the spec")
    return [run(places["v1"], "prepare")["pair"]], [None]


def parent_changes_arrive_in_the_base(base: str) -> tuple:
    places = world(base)
    mate_push(places, "develop", "team.txt", "new\n")
    got = run(places["v1"], "prepare")
    second = git(places["v1"], "rev-parse", f"{got['base']}^2")
    return ([got["status"], got["parent_commits"], second == git(places["remote"], "rev-parse", "develop"),
             git(places["v1"], "rev-parse", "HEAD^") == got["base"]],
            ["ready", 1, True, True])


def base_conflict_resolves_with_a_trailer(base: str) -> tuple:
    places = world(base)
    mate_push(places, "develop", "shared.txt", "one\nTWO-develop\nthree\n")
    mate_push(places, "feature/x", "shared.txt", "one\nTWO-feature\nthree\n")
    stopped = run(places["v1"], "prepare")
    write(places["v1"], "shared.txt", "one\nTWO-both\nthree\n")
    git(places["v1"], "add", "shared.txt")
    got = run(places["v1"], "continue", "--clash", "shared.txt: kept both edits")
    return ([stopped["status"], stopped["phase"], stopped["files"], got["status"], got["clashes"]],
            ["conflict", "base", ["shared.txt"], "ready", ["shared.txt: kept both edits"]])


def rebase_conflict_resolves_with_a_trailer(base: str) -> tuple:
    places = world(base)
    stopped = rebase_conflict(places)
    write(places["v1"], "app1.txt", "a\nb\nc\n")
    git(places["v1"], "add", "app1.txt")
    got = run(places["v1"], "continue", "--clash", "app1.txt: the plan's version wins")
    return ([stopped["status"], stopped["phase"], got["status"], got["clashes"],
             git(places["v1"], "symbolic-ref", "--short", "HEAD")],
            ["conflict", "rebase", "ready", ["app1.txt: the plan's version wins"], "worktree-v1"])


def continue_refuses_unmerged_files(base: str) -> tuple:
    places = world(base)
    rebase_conflict(places)
    got = run(places["v1"], "continue")
    return [got["status"], got["files"], "unmerged" in got["problem"]], ["refused", ["app1.txt"], True]


def continue_refuses_conflict_markers(base: str) -> tuple:
    places = world(base)
    rebase_conflict(places)
    git(places["v1"], "add", "app1.txt")
    got = run(places["v1"], "continue")
    return [got["status"], got["files"], "markers" in got["problem"]], ["refused", ["app1.txt"], True]


def prepare_refuses_an_open_conflict(base: str) -> tuple:
    places = world(base)
    rebase_conflict(places)
    got = run(places["v1"], "prepare")
    return [got["status"], "continue" in got["problem"]], ["refused", True]


def abort_returns_to_the_branch(base: str) -> tuple:
    places = world(base)
    tip = git(places["v1"], "rev-parse", "HEAD")
    rebase_conflict(places)
    got = run(places["v1"], "abort")
    return ([got["status"], got["branch"], git(places["v1"], "rev-parse", "HEAD") == tip],
            ["aborted", "worktree-v1", True])


def land_merges_once_and_pushes(base: str) -> tuple:
    places = world(base)
    ready = run(places["v1"], "prepare")
    got = run(places["v1"], "land", "--tip", ready["tip"], "--title", "Demo")
    head = remote_head(places)
    return ([got["status"], got["merge"] == head, git(places["remote"], "log", "-1", "--format=%s", head),
             git(places["remote"], "rev-parse", f"{head}^1") == ready["base"],
             git(places["remote"], "rev-parse", f"{head}^2") == ready["tip"]],
            ["landed", True, "Merge worktree-v1: Demo", True, True])


def packet_names_the_push_target(base: str) -> tuple:
    return [run(world(base)["v1"], "prepare")["target"]], ["origin/feature/x"]


def land_needs_a_packet(base: str) -> tuple:
    got = run(world(base)["v1"], "land", "--tip", "0" * 40)
    return [got["status"], "prepare first" in got["problem"]], ["stale", True]


def land_needs_the_reviewed_tip(base: str) -> tuple:
    places = world(base)
    run(places["v1"], "prepare")
    before = remote_head(places)
    got = run(places["v1"], "land", "--tip", "0" * 40)
    return [got["status"], remote_head(places) == before], ["stale", True]


def tampered_base_is_refused(base: str) -> tuple:
    places = world(base)
    ready = run(places["v1"], "prepare")
    tree = git(places["v1"], "rev-parse", "HEAD^{tree}")
    stray = git(places["v1"], "commit-tree", tree, "-m", "stray")
    path = os.path.join(git(places["v1"], "rev-parse", "--path-format=absolute", "--git-dir"), "merge-worktree.json")
    with open(path, encoding="utf-8") as handle:
        state = json.load(handle)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state | {"base": stray}, handle)
    before = remote_head(places)
    got = run(places["v1"], "land", "--tip", ready["tip"])
    return [got["status"], remote_head(places) == before], ["refused", True]


def failed_push_keeps_the_packet(base: str) -> tuple:
    places = world(base)
    ready = run(places["v1"], "prepare")
    hook(places["remote"], "pre-receive")
    refused = run(places["v1"], "land", "--tip", ready["tip"])
    os.remove(os.path.join(places["remote"], "hooks", "pre-receive"))
    got = run(places["v1"], "land", "--tip", ready["tip"])
    return [refused["status"], got["status"]], ["refused", "landed"]


def land_after_a_new_commit_is_stale(base: str) -> tuple:
    places = world(base)
    run(places["v1"], "prepare")
    write(places["v1"], "late.txt", "late\n", "late change")
    before = remote_head(places)
    got = run(places["v1"], "land", "--tip", git(places["v1"], "rev-parse", "HEAD^"))
    return [got["status"], remote_head(places) == before], ["stale", True]


def second_worktree_lands_after_a_rejected_push(base: str) -> tuple:
    places = world(base)
    v2 = add_worktree(places, 2)
    one = run(places["v1"], "prepare")
    two = run(v2, "prepare")
    first = run(places["v1"], "land", "--tip", one["tip"])
    rejected = run(v2, "land", "--tip", two["tip"])
    retried = run(v2, "land", "--tip", two["tip"])
    again = run(v2, "prepare")
    second = run(v2, "land", "--tip", again["tip"])
    head = remote_head(places)
    both = all(subprocess.run(["git", "-C", places["remote"], "merge-base", "--is-ancestor", tip, head],
                              env=ENV).returncode == 0 for tip in (first["merge"], again["tip"]))
    return ([first["status"], rejected["status"], retried["status"], again["status"], second["status"], both],
            ["landed", "rejected", "stale", "ready", "landed", True])


def landed_work_reports_merged(base: str) -> tuple:
    places = world(base)
    landed(places)
    return [run(places["v1"], "prepare")["status"]], ["merged"]


def cleanup_refuses_before_landing(base: str) -> tuple:
    places = world(base)
    got = run(places["v1"], "cleanup")
    return [got["status"], os.path.isdir(places["v1"])], ["refused", True]


def cleanup_removes_the_worktree_and_branch(base: str) -> tuple:
    places = world(base)
    landed(places)
    got = run(places["v1"], "cleanup")
    branches = git(places["main"], "branch", "--list", "worktree-v1")
    return [got["status"], os.path.isdir(places["v1"]), branches], ["removed", False, ""]


def herdr_cleanup(base: str, mode: str = "ok") -> tuple[dict, dict, list[str], dict]:
    """Land v1, then clean up under a fake Herdr: the reply, the finish log, Herdr's calls, and the places."""
    places = world(base)
    landed(places)
    bin_dir, log = os.path.join(base, "bin"), os.path.join(base, "herdr.log")
    os.makedirs(bin_dir)
    with open(os.path.join(bin_dir, "herdr"), "w", encoding="utf-8") as handle:
        handle.write(FAKE_HERDR)
    os.chmod(os.path.join(bin_dir, "herdr"), 0o755)
    env = ENV | {"HERDR_ENV": "1", "PATH": f"{bin_dir}{os.pathsep}{ENV['PATH']}", "FAKE_HERDR_LOG": log,
                 "FAKE_WORKTREE": places["v1"], "FAKE_MAIN": places["main"], "FAKE_HERDR_MODE": mode}
    got = run(places["v1"], "cleanup", env=env)
    deadline = time.monotonic() + 20
    while not os.path.exists(got["log"]) and time.monotonic() < deadline:
        time.sleep(0.1)
    with open(log, encoding="utf-8") as handle:
        calls = [line.split()[1] for line in handle]
    with open(got["log"], encoding="utf-8") as handle:
        finished = json.load(handle)
    return got, finished, calls, places


def cleanup_goes_through_herdr(base: str) -> tuple:
    got, finished, calls, places = herdr_cleanup(base)
    return ([got["status"], got["workspace"], calls, finished["status"], os.path.isdir(places["v1"]),
             git(places["main"], "branch", "--list", "worktree-v1")],
            ["removing", "w7", ["list", "remove"], "removed", False, ""])


def failed_herdr_remove_is_logged_and_keeps_the_branch(base: str) -> tuple:
    got, finished, _, places = herdr_cleanup(base, "fail")
    return ([got["status"], finished["status"], "branch" in finished, os.path.isdir(places["v1"]),
             bool(git(places["main"], "branch", "--list", "worktree-v1"))],
            ["removing", "refused", False, True, True])


def cleanup_runs_from_outside_with_the_worktree_option(base: str) -> tuple:
    places = world(base)
    landed(places)
    got = run(places["main"], "--worktree", places["v1"], "cleanup")
    return [got["status"], os.path.isdir(places["v1"])], ["removed", False]


def empty_resolution(base: str, *notes: str) -> dict:
    """v1's second commit edits a line the teammate also edits; resolving to the teammate's leaves it empty."""
    places = world(base)
    write(places["v1"], "shared.txt", "one\nTWO-worktree\nthree\n", "worktree edits shared.txt")
    mate_push(places, "feature/x", "shared.txt", "one\nTWO-feature\nthree\n")
    run(places["v1"], "prepare")
    write(places["v1"], "shared.txt", "one\nTWO-feature\nthree\n")
    git(places["v1"], "add", "shared.txt")
    return run(places["v1"], "continue", *notes)


def empty_resolution_keeps_its_clash_note(base: str) -> tuple:
    got = empty_resolution(base, "--clash", "shared.txt: the feature's line wins")
    return [got["status"], got["commits"], got["clashes"], got["warnings"]], \
        ["ready", 2, ["shared.txt: the feature's line wins"], []]


def empty_resolution_without_notes_is_dropped(base: str) -> tuple:
    got = empty_resolution(base)
    return [got["status"], got["commits"], len(got["warnings"])], ["ready", 1, 1]


def no_feature_branch_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "--unset", "branch.worktree-v1.parent")
    git(places["main"], "switch", "-q", "--detach")
    got = run(places["v1"], "prepare")
    return [got["status"], "no feature branch" in got["problem"]], ["refused", True]


def default_branch_is_never_a_fallback(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "--unset", "branch.worktree-v1.parent")
    git(places["main"], "switch", "-q", "develop")
    got = run(places["v1"], "prepare")
    return [got["status"], "default branch" in got["problem"]], ["refused", True]


def parent_cannot_be_the_feature(base: str) -> tuple:
    got = run(world(base)["v1"], "prepare", "--parent", "feature/x")
    return [got["status"]], ["refused"]


def unsafe_parent_is_never_stored(base: str) -> tuple:
    places = world(base)
    got = run(places["v1"], "prepare", "--parent", "+develop:refs/heads/x")
    return ([got["status"], "cannot be the parent" in got["problem"], git(places["main"], "config", "branch.feature/x.parent")],
            ["refused", True, "develop"])


def failed_rebase_is_undone(base: str) -> tuple:
    places = world(base)
    tip = git(places["v1"], "rev-parse", "HEAD")
    mate_push(places, "feature/x", "team.txt", "new\n")
    hook(os.path.join(places["main"], ".git"), "pre-rebase")
    got = run(places["v1"], "prepare")
    return ([got["status"], git(places["v1"], "symbolic-ref", "--short", "HEAD"), git(places["v1"], "rev-parse", "HEAD") == tip],
            ["refused", "worktree-v1", True])


def failed_base_merge_is_undone(base: str) -> tuple:
    places = world(base)
    tip = git(places["v1"], "rev-parse", "HEAD")
    mate_push(places, "develop", "team.txt", "new\n")
    hook(os.path.join(places["main"], ".git"), "pre-merge-commit")
    got = run(places["v1"], "prepare")
    return ([got["status"], git(places["v1"], "symbolic-ref", "-q", "--short", "HEAD"), git(places["v1"], "rev-parse", "HEAD") == tip],
            ["refused", "worktree-v1", True])


def continue_needs_an_open_conflict(base: str) -> tuple:
    got = run(world(base)["v1"], "continue")
    return [got["status"], "no conflict" in got["problem"]], ["refused", True]


def continue_needs_staged_files(base: str) -> tuple:
    places = world(base)
    rebase_conflict(places)
    write(places["v1"], "app1.txt", "a\nb\nc\n")
    git(places["v1"], "add", "app1.txt")
    git(places["v1"], "restore", "--staged", "app1.txt")
    got = run(places["v1"], "continue")
    return [got["status"], got["files"], "not staged" in got["problem"]], ["refused", ["app1.txt"], True]


def rebase_keeps_the_author(base: str) -> tuple:
    places = world(base)
    git(places["v1"], "commit", "-q", "--amend", "--no-edit", "--author", "Alice <alice@example.com>")
    rebase_conflict(places)
    write(places["v1"], "app1.txt", "a\nb\nc\n")
    git(places["v1"], "add", "app1.txt")
    run(places["v1"], "continue", "--clash", "app1.txt: ours")
    return [git(places["v1"], "log", "-1", "--format=%an %s")], ["Alice build v1"]


def parent_history_notes_stay_out(base: str) -> tuple:
    places = world(base)
    mate = places["mate"]
    git(mate, "fetch", "-q", "origin")
    git(mate, "switch", "-q", "-C", "develop", "origin/develop")
    write(mate, "old.txt", "x\n")
    git(mate, "add", "old.txt")
    git(mate, "commit", "-q", "-m", "older work", "--trailer", "Clash-resolved: old.txt: someone else's call")
    git(mate, "push", "-q", "origin", "develop")
    return [run(places["v1"], "prepare")["clashes"]], [[]]


def staging_rerere_still_stops_for_review(base: str) -> tuple:
    places = world(base)
    tip = git(places["v1"], "rev-parse", "HEAD")
    git(places["main"], "config", "rerere.enabled", "true")
    git(places["main"], "config", "rerere.autoUpdate", "true")
    rebase_conflict(places)
    write(places["v1"], "app1.txt", "a\nb\nc\n")
    git(places["v1"], "add", "app1.txt")
    run(places["v1"], "continue", "--clash", "app1.txt: ours")
    git(places["v1"], "reset", "-q", "--hard", tip)
    got = run(places["v1"], "prepare")
    return [got["status"], got["replayed"]], ["conflict", ["app1.txt"]]


def heading_rule_is_not_a_marker(base: str) -> tuple:
    places = world(base)
    mate_push(places, "develop", "doc.md", "Title\n=======\n\ntext\n")
    mate_push(places, "develop", "shared.txt", "one\nTWO-develop\nthree\n")
    mate_push(places, "feature/x", "shared.txt", "one\nTWO-feature\nthree\n")
    run(places["v1"], "prepare")
    write(places["v1"], "shared.txt", "one\nTWO-both\nthree\n")
    git(places["v1"], "add", "shared.txt")
    return [run(places["v1"], "continue", "--clash", "shared.txt: both")["status"]], ["ready"]


def narrow_fetch_config_still_sees_the_remote(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "remote.origin.fetch", "+refs/heads/develop:refs/remotes/origin/develop")
    mate_push(places, "feature/x", "team.txt", "new\n")
    got = run(places["v1"], "prepare")
    return [got["status"], got["base"] == remote_head(places)], ["ready", True]


def renames_and_edits_are_listed_whole(base: str) -> tuple:
    v1 = world(base)["v1"]
    write(v1, "app1.txt", "a\nb\nc\nd\n")
    git(v1, "mv", "shared.txt", "zz.txt")
    return [run(v1, "prepare")["files"]], [["app1.txt", "zz.txt"]]


def cleanup_refuses_untracked_files(base: str) -> tuple:
    places = world(base)
    landed(places)
    write(places["v1"], "notes.txt", "draft\n")
    got = run(places["v1"], "cleanup")
    return [got["status"], got["files"], os.path.isdir(places["v1"])], ["refused", ["notes.txt"], True]


def cleanup_asks_before_dropping_ignored_files(base: str) -> tuple:
    places = world(base)
    landed(places)
    with open(os.path.join(places["main"], ".git", "info", "exclude"), "a", encoding="utf-8") as handle:
        handle.write("*.env\n")
    write(places["v1"], "secret.env", "key\n")
    asked = run(places["v1"], "cleanup")
    got = run(places["v1"], "cleanup", "--drop-ignored")
    return [asked["status"], asked["files"], got["status"], os.path.isdir(places["v1"])], \
        ["refused", ["secret.env"], "removed", False]


def hand_made_worktree_uses_the_main_branch(base: str) -> tuple:
    places = world(base)
    git(places["main"], "config", "--unset", "branch.worktree-v1.parent")
    got = run(places["v1"], "prepare")
    return [got["status"], got["feature"]], ["ready", "feature/x"]


def failed_fetch_is_refused(base: str) -> tuple:
    places = world(base)
    git(places["main"], "remote", "set-url", "origin", os.path.join(base, "gone.git"))
    got = run(places["v1"], "prepare")
    return [got["status"], got["problem"].startswith("fetching origin failed")], ["refused", True]


CASES = [
    main_checkout_is_refused,
    detached_head_is_refused,
    uncommitted_work_is_listed,
    unpushed_feature_is_refused,
    parent_is_asked_once,
    packet_reports_the_work,
    plan_without_spec_is_not_a_pair,
    parent_changes_arrive_in_the_base,
    base_conflict_resolves_with_a_trailer,
    rebase_conflict_resolves_with_a_trailer,
    continue_refuses_unmerged_files,
    continue_refuses_conflict_markers,
    prepare_refuses_an_open_conflict,
    abort_returns_to_the_branch,
    land_merges_once_and_pushes,
    land_needs_a_packet,
    land_after_a_new_commit_is_stale,
    second_worktree_lands_after_a_rejected_push,
    landed_work_reports_merged,
    cleanup_refuses_before_landing,
    cleanup_removes_the_worktree_and_branch,
    cleanup_goes_through_herdr,
    failed_herdr_remove_is_logged_and_keeps_the_branch,
    cleanup_runs_from_outside_with_the_worktree_option,
    empty_resolution_keeps_its_clash_note,
    empty_resolution_without_notes_is_dropped,
    packet_names_the_push_target,
    land_needs_the_reviewed_tip,
    tampered_base_is_refused,
    failed_push_keeps_the_packet,
    no_feature_branch_is_refused,
    default_branch_is_never_a_fallback,
    parent_cannot_be_the_feature,
    unsafe_parent_is_never_stored,
    failed_rebase_is_undone,
    failed_base_merge_is_undone,
    continue_needs_an_open_conflict,
    continue_needs_staged_files,
    rebase_keeps_the_author,
    parent_history_notes_stay_out,
    staging_rerere_still_stops_for_review,
    heading_rule_is_not_a_marker,
    narrow_fetch_config_still_sees_the_remote,
    renames_and_edits_are_listed_whole,
    cleanup_refuses_untracked_files,
    cleanup_asks_before_dropping_ignored_files,
    hand_made_worktree_uses_the_main_branch,
    failed_fetch_is_refused,
]


def check(case) -> str | None:
    """Run one case in its own temporary folder; the failure text, or None when it holds."""
    with tempfile.TemporaryDirectory() as base:
        try:
            got, want = case(os.path.realpath(base))
        except (AssertionError, ValueError, KeyError, subprocess.CalledProcessError) as error:
            return f"{case.__name__}: {error}"
    return None if got == want else f"{case.__name__}: got {got!r}, want {want!r}"


def main() -> int:
    # Cases share nothing, so they run side by side; the wait is on git processes, not Python.
    with concurrent.futures.ThreadPoolExecutor() as pool:
        failures = [f for f in pool.map(check, CASES) if f]
    if failures:
        print("\n\n".join(failures))
        print(f"\n{len(failures)} failure(s)")
        return 1
    print(f"ok: {len(CASES)} merge rules hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
