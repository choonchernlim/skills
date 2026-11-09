#!/usr/bin/env python3
"""Self-test for new_worktree.py.

Purpose: prove each worktree rule against throwaway git repositories and a fake
herdr command, so a change cannot cut a worktree from the wrong base, lose
carried work, or skip Herdr's sidebar.
Usage: python3 scripts/test_new_worktree.py
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "new_worktree.py")
# Drop inherited GIT_* and HERDR_* variables, so neither a hook nor a Herdr pane steers the fixtures,
# and stop git's repository search at the temp folder, so a fixture never finds a repository above it.
ENV = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "HERDR_"))} | {
    "GIT_CEILING_DIRECTORIES": os.path.realpath(tempfile.gettempdir()),
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}
# A stand-in for herdr: logs each call, and in "ok" mode creates the worktree as Herdr would.
FAKE_HERDR = f"""#!{sys.executable}
import json, os, subprocess, sys
args = sys.argv[1:]
with open(os.environ["FAKE_HERDR_LOG"], "a") as log:
    log.write(" ".join(args[:2]) + "\\n")
mode = os.environ["FAKE_HERDR_MODE"]
if args[:2] == ["pane", "current"]:
    sys.exit(1 if mode == "no-pane" else 0)
if args[:2] == ["worktree", "create"]:
    if mode == "fail-create":
        sys.exit("worktree create failed")
    opt = dict(zip(args[2::2], args[3::2]))
    subprocess.run(["git", "-C", opt["--cwd"], "worktree", "add", "-q", "-b", opt["--branch"], opt["--path"], opt["--base"]], check=True)
    print(json.dumps({{"result": {{"workspace": {{"workspace_id": "w9"}}, "root_pane": {{"pane_id": "w9:p1"}}}}}}))
"""


def git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True, env=ENV).stdout.strip()


def repo(base: str, name: str = "repo") -> str:
    root = os.path.join(base, name)
    os.makedirs(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "commit", "-q", "--allow-empty", "-m", "start")
    return root


def worktree(root: str, branch: str, folder: str = "side") -> str:
    """A linked worktree beside the main checkout, on a new branch."""
    path = os.path.join(os.path.dirname(root), folder)
    git(root, "worktree", "add", "-q", "-b", branch, path)
    return path


def write(root: str, path: str, text: str = "# Fixture\n", commit: bool = True) -> None:
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)
    if commit:
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", f"add {path}")


def read(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def clone(base: str) -> tuple[str, str]:
    """A bare remote and a clone of it on main, tracking origin/main."""
    remote = os.path.join(base, "remote.git")
    git(base, "init", "-q", "--bare", "-b", "main", remote)
    root = repo(base)
    git(root, "remote", "add", "origin", remote)
    git(root, "push", "-q", "-u", "origin", "main")
    return remote, root


def push_from_elsewhere(base: str, remote: str, path: str) -> None:
    other = os.path.join(base, "other")
    git(base, "clone", "-q", remote, other)
    write(other, path)
    git(other, "push", "-q", "origin", "main")


def call(cwd: str, *args: str, herdr: str | None = None) -> subprocess.CompletedProcess:
    env = dict(ENV)
    if herdr:
        bin_dir = os.path.join(os.path.dirname(cwd), "bin")
        os.makedirs(bin_dir, exist_ok=True)
        fake = os.path.join(bin_dir, "herdr")
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write(FAKE_HERDR)
        os.chmod(fake, 0o755)
        env |= {"HERDR_ENV": "1", "PATH": bin_dir + os.pathsep + env["PATH"],
                "FAKE_HERDR_MODE": herdr, "FAKE_HERDR_LOG": os.path.join(bin_dir, "log")}
    return subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd, capture_output=True, text=True, env=env)


def run(cwd: str, *args: str, herdr: str | None = None) -> dict:
    done = call(cwd, *args, herdr=herdr)
    if done.returncode:
        raise AssertionError(f"exit {done.returncode}: {done.stderr.strip()}")
    return json.loads(done.stdout)


def reservations(root: str) -> str:
    return git(root, "for-each-ref", "--format=%(refname)", "refs/grill-me")


def herdr_calls(root: str) -> list[str]:
    return (read(os.path.join(os.path.dirname(root), "bin", "log")) or "").splitlines()


def plain_repo_offers_nothing(base: str) -> tuple:
    return run(repo(base), "--check"), {"offer": False}


def ignored_worktree_folder_offers(base: str) -> tuple:
    root = repo(base)
    write(root, ".gitignore", ".claude/worktrees/\n")
    return run(root, "--check"), {"offer": True}


def live_worktree_offers(base: str) -> tuple:
    root = repo(base)
    worktree(root, "side")
    return run(root, "--check"), {"offer": True}


def deleted_worktree_offers_nothing(base: str) -> tuple:
    root = repo(base)
    shutil.rmtree(worktree(root, "side"))
    return run(root, "--check"), {"offer": False}


def linked_worktree_never_offers(base: str) -> tuple:
    root = repo(base)
    write(root, ".gitignore", ".claude/worktrees/\n")
    return run(worktree(root, "side"), "--check"), {"offer": False}


def topic_cuts_from_current_branch(base: str) -> tuple:
    root = repo(base)
    git(root, "switch", "-q", "-c", "feature/x")
    write(root, "app.txt")
    got = run(root, "--topic", "Order Export")
    path = os.path.join(root, ".claude/worktrees/v1")
    return ([got["version"], got["path"], got["method"], got["branch"], got["spec"], got["plan"], got["handoff"],
             got["problem"], git(path, "rev-parse", "HEAD") == git(root, "rev-parse", "HEAD"),
             git(root, "config", "branch.worktree-v1.parent"), reservations(root)],
            [1, path, "git", "worktree-v1", f"{path}/specs/v001-order-export/spec.md",
             f"{path}/specs/v001-order-export/plan.md", None, None, True, "feature/x", ""])


def version_releases_its_reservation(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v004-x/spec.md")
    git(root, "update-ref", "refs/grill-me/v4", "HEAD")
    got = run(root, "--version", "4")
    return [got["spec"], got["problem"], reservations(root)], [f"{got['path']}/specs/v004-x/spec.md", None, ""]


def missing_tracking_ref_warns_and_frees_nothing(base: str) -> tuple:
    remote, root = clone(base)
    git(root, "update-ref", "-d", "refs/remotes/origin/main")
    git(root, "config", "--unset-all", "remote.origin.fetch")
    got = run(root, "--topic", "Single")
    return ([got["problem"], got["method"], got["warnings"], reservations(root)],
            [None, "git", ["main keeps no remote-tracking copy of its upstream, so the worktree starts at HEAD"], ""])


def failed_git_call_reports_and_frees_its_version(base: str) -> tuple:
    root = os.path.join(base, "unborn")
    os.makedirs(root)
    git(root, "init", "-q", "-b", "main")
    got = run(root, "--topic", "Unborn")
    return [bool(got["problem"]), got["version"], reservations(root)], [True, 1, ""]


def refused_topic_frees_its_version(base: str) -> tuple:
    root = repo(base)
    os.makedirs(os.path.join(root, ".claude/worktrees/v1"))
    got = run(root, "--topic", "Blocked")
    return [got["problem"], reservations(root)], [".claude/worktrees/v1 already exists", ""]


def worktree_folder_is_excluded_once(base: str) -> tuple:
    root = repo(base)
    run(root, "--topic", "One")
    run(root, "--topic", "Two")
    return [git(root, "status", "--porcelain"), read(os.path.join(root, ".git/info/exclude")).count(".claude/worktrees/")], ["", 1]


def ignored_folder_is_not_excluded(base: str) -> tuple:
    root = repo(base)
    write(root, ".gitignore", ".claude/worktrees/\n")
    run(root, "--topic", "One")
    return [(read(os.path.join(root, ".git/info/exclude")) or "").count(".claude/worktrees/")], [0]


def linked_worktree_is_refused(base: str) -> tuple:
    got = run(worktree(repo(base), "side"), "--topic", "Nested")
    return [got["problem"], got["version"]], ["this is already a linked worktree; plan here instead", None]


def existing_branch_is_refused(base: str) -> tuple:
    root = repo(base)
    git(root, "branch", "worktree-v6")
    return [run(root, "--version", "6")["problem"]], ["branch worktree-v6 already exists"]


def version_below_one_is_rejected(base: str) -> tuple:
    return [call(repo(base), "--version", "0").returncode], [2]


def behind_branch_cuts_from_upstream(base: str) -> tuple:
    remote, root = clone(base)
    before = git(root, "rev-parse", "HEAD")
    push_from_elsewhere(base, remote, "teammate.txt")
    got = run(root, "--topic", "Fresh")
    return ([got["warnings"], os.path.exists(os.path.join(got["path"], "teammate.txt")), git(root, "rev-parse", "HEAD") == before],
            [[], True, True])


def diverged_branch_warns_and_uses_head(base: str) -> tuple:
    remote, root = clone(base)
    push_from_elsewhere(base, remote, "teammate.txt")
    write(root, "mine.txt")
    got = run(root, "--topic", "Diverged")
    return ([got["warnings"], os.path.exists(os.path.join(got["path"], "mine.txt"))],
            [["main and its upstream have diverged, so the worktree starts at HEAD"], True])


def failed_fetch_warns_and_uses_head(base: str) -> tuple:
    remote, root = clone(base)
    shutil.rmtree(remote)
    got = run(root, "--topic", "Offline")
    return [len(got["warnings"]), got["warnings"][0].startswith("fetching origin failed"), got["method"]], [1, True, "git"]


def detached_head_records_no_parent(base: str) -> tuple:
    root = repo(base)
    git(root, "switch", "-q", "--detach")
    got = run(root, "--topic", "Detached")
    return ([got["warnings"], subprocess.run(["git", "-C", root, "config", "branch.worktree-v1.parent"], env=ENV,
                                              capture_output=True).returncode],
            [["HEAD is detached, so no parent branch is recorded"], 1])


def carry_moves_uncommitted_changes(base: str) -> tuple:
    root = repo(base)
    write(root, "src/app.txt", "old\n")
    write(root, "src/gone.txt")
    write(root, "src/app.txt", "new\n", commit=False)
    os.remove(os.path.join(root, "src/gone.txt"))
    write(root, "specs/v009-x/spec.md", commit=False)
    got = run(root, "--version", "9", "--carry", "src", "specs")
    path = got["path"]
    return ([sorted(got["carried"]), got["spec"], read(os.path.join(path, "src/app.txt")),
             os.path.exists(os.path.join(path, "src/gone.txt")), git(root, "status", "--porcelain"),
             os.path.exists(os.path.join(root, "specs"))],
            [["specs/v009-x/spec.md", "src/app.txt", "src/gone.txt"], f"{path}/specs/v009-x/spec.md", "new\n", False, "", False])


def carry_reads_names_literally(base: str) -> tuple:
    root = repo(base)
    write(root, "app/[id]/page.tsx", "old\n")
    write(root, "app/i/page.tsx", "old\n")
    write(root, "app/[id]/page.tsx", "mine\n", commit=False)
    write(root, "app/i/page.tsx", "other edit\n", commit=False)
    got = run(root, "--version", "4", "--carry", "app/[id]/page.tsx")
    return ([got["carried"], read(os.path.join(root, "app/i/page.tsx")), read(os.path.join(got["path"], "app/[id]/page.tsx"))],
            [["app/[id]/page.tsx"], "other edit\n", "mine\n"])


def carry_refuses_split_staged_edits(base: str) -> tuple:
    root = repo(base)
    write(root, "app.txt", "old\n")
    write(root, "app.txt", "staged\n", commit=False)
    git(root, "add", "app.txt")
    write(root, "app.txt", "unstaged\n", commit=False)
    got = run(root, "--version", "5", "--carry", "app.txt")
    return ([got["problem"].startswith("cannot carry app.txt: it has staged and unstaged edits"),
             git(root, "show", ":app.txt"), read(os.path.join(root, "app.txt"))], [True, "staged", "unstaged\n"])


def carry_cuts_from_head_not_upstream(base: str) -> tuple:
    remote, root = clone(base)
    write(root, "app.txt", "old\n")
    git(root, "push", "-q")
    other = os.path.join(base, "other")
    git(base, "clone", "-q", remote, other)
    write(other, "app.txt", "teammate\n")
    git(other, "push", "-q")
    write(root, "app.txt", "mine\n", commit=False)
    got = run(root, "--version", "3", "--carry", "app.txt")
    return ([read(os.path.join(got["path"], "app.txt")), git(got["path"], "rev-parse", "HEAD") == git(root, "rev-parse", "HEAD")],
            ["mine\n", True])


def carry_never_writes_through_a_symlink(base: str) -> tuple:
    root = repo(base)
    outside = os.path.join(base, "outside.txt")
    write(root, "outside.txt", "safe\n", commit=False)
    shutil.move(os.path.join(root, "outside.txt"), outside)
    os.symlink(outside, os.path.join(root, "notes.md"))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "link")
    os.remove(os.path.join(root, "notes.md"))
    write(root, "notes.md", "carried\n", commit=False)
    got = run(root, "--version", "3", "--carry", "notes.md")
    return ([got["problem"], got["carried"], read(outside), read(os.path.join(root, "notes.md"))],
            ["cannot carry notes.md: the worktree holds a symlink on its path; the worktree exists, but nothing moved",
             [], "safe\n", "carried\n"])


def unsafe_agent_kind_is_rejected(base: str) -> tuple:
    return [call(repo(base), "--topic", "X", "--agent=-x;rm").returncode], [2]


def carry_outside_checkout_is_refused(base: str) -> tuple:
    root = repo(base)
    outside = run(root, "--version", "9", "--carry", "../elsewhere")["problem"]
    inside = run(root, "--version", "9", "--carry", ".claude/worktrees/v1")["problem"]
    return [outside.startswith("--carry paths"), inside.startswith("--carry paths"),
            os.path.exists(os.path.join(root, ".claude/worktrees/v9"))], [True, True, False]


def herdr_creates_and_hands_off(base: str) -> tuple:
    root = repo(base)
    got = run(root, "--topic", "In Herdr", "--agent", "codex", herdr="ok")
    return ([got["method"], got["handoff"], got["warnings"], herdr_calls(root)],
            ["herdr", "herdr agent start repo-v1 --kind codex --pane w9:p1 && "
                      "herdr agent prompt repo-v1 '/grill-me resume specs/v001-in-herdr/spec.md'",
             [], ["pane current", "worktree create"]])


def failed_herdr_stops_and_frees_its_version(base: str) -> tuple:
    root = repo(base)
    got = run(root, "--topic", "Broken", herdr="fail-create")
    return ([got["problem"].startswith("herdr worktree create failed"), os.path.exists(got["path"]), reservations(root)],
            [True, False, ""])


def herdr_is_skipped_without_its_pane(base: str) -> tuple:
    root = repo(base)
    got = run(root, "--topic", "No Pane", herdr="no-pane")
    return [got["method"], got["handoff"], herdr_calls(root)], ["git", None, ["pane current"]]


CASES = [
    plain_repo_offers_nothing,
    ignored_worktree_folder_offers,
    live_worktree_offers,
    deleted_worktree_offers_nothing,
    linked_worktree_never_offers,
    topic_cuts_from_current_branch,
    version_releases_its_reservation,
    missing_tracking_ref_warns_and_frees_nothing,
    failed_git_call_reports_and_frees_its_version,
    refused_topic_frees_its_version,
    worktree_folder_is_excluded_once,
    ignored_folder_is_not_excluded,
    linked_worktree_is_refused,
    existing_branch_is_refused,
    version_below_one_is_rejected,
    behind_branch_cuts_from_upstream,
    diverged_branch_warns_and_uses_head,
    failed_fetch_warns_and_uses_head,
    detached_head_records_no_parent,
    carry_moves_uncommitted_changes,
    carry_cuts_from_head_not_upstream,
    carry_reads_names_literally,
    carry_refuses_split_staged_edits,
    carry_never_writes_through_a_symlink,
    unsafe_agent_kind_is_rejected,
    carry_outside_checkout_is_refused,
    herdr_creates_and_hands_off,
    failed_herdr_stops_and_frees_its_version,
    herdr_is_skipped_without_its_pane,
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
    print(f"ok: {len(CASES)} worktree rules hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
