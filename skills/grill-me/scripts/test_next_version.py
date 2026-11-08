#!/usr/bin/env python3
"""Self-test for next_version.py.

Purpose: prove each version rule against throwaway git repositories, so a
change cannot silently hand two specs one number.
Usage: python3 scripts/test_next_version.py
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "next_version.py")
# Drop inherited GIT_* variables, so a hook's GIT_DIR never points the fixtures at the real checkout,
# and stop git's repository search at the temp folder, so a fixture never finds a repository above it.
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
    return subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True, env=ENV).stdout


def repo(base: str) -> str:
    root = os.path.join(base, "repo")
    os.makedirs(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "commit", "-q", "--allow-empty", "-m", "start")
    return root


def worktree(root: str, branch: str, folder: str = "wt") -> str:
    """A linked worktree beside the main checkout, on a new branch."""
    path = os.path.join(os.path.dirname(root), folder)
    git(root, "worktree", "add", "-q", "-b", branch, path)
    return path


def write(root: str, *paths: str, commit: bool = True) -> None:
    for path in paths:
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write("# Fixture\n")
    if commit:
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "add " + " ".join(paths))


def on_branch(root: str, branch: str, *paths: str) -> None:
    """Commit files on another branch, then return to main, so only history holds them."""
    git(root, "switch", "-q", "-c", branch)
    write(root, *paths)
    git(root, "switch", "-q", "main")


def call(cwd: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd, capture_output=True, text=True, env=ENV)


def run(cwd: str, *args: str) -> dict:
    done = call(cwd, *args)
    if done.returncode:
        raise AssertionError(f"exit {done.returncode}: {done.stderr.strip()}")
    return json.loads(done.stdout)


def reservations(root: str) -> list[str]:
    return git(root, "for-each-ref", "--format=%(refname)", "refs/grill-me").split()


def empty_repo_starts_at_one(base: str) -> tuple:
    return (run(repo(base), "--topic", "Order Export"),
            {"version": 1, "source": "next", "folder": "specs/v001-order-export",
             "spec": "specs/v001-order-export/spec.md", "plan": "specs/v001-order-export/plan.md",
             "existing": [], "problem": None})


def running_lists_never_count(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v001-alpha/spec.md", "specs/v003-beta/plan.md", "specs/v9999-todo/spec.md", "specs/README.md")
    return run(root, "--topic", "Next")["version"], 4


def unpadded_folders_count(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v12-legacy/spec.md")
    return run(root, "--topic", "Next")["folder"], "specs/v013-next"


def other_branches_count(base: str) -> tuple:
    root = repo(base)
    on_branch(root, "side", "specs/v005-gamma/plan.md")
    return run(root, "--topic", "Next")["version"], 6


def non_ascii_folder_on_branch_counts(base: str) -> tuple:
    root = repo(base)
    on_branch(root, "side", "specs/v020-caf\u00e9/spec.md")
    return run(root, "--topic", "Next")["version"], 21


def uncommitted_folder_counts(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v002-delta/spec.md", commit=False)
    return run(root, "--topic", "Next")["version"], 3


def reserved_branch_is_skipped(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v002-golf/spec.md")
    git(root, "branch", "worktree/v4")
    return run(root, "--topic", "Next")["version"], 5


def each_run_reserves_a_new_version(base: str) -> tuple:
    root = repo(base)
    first, second = run(root, "--topic", "Lima"), run(root, "--topic", "Mike")
    return ([first["version"], second["version"], reservations(root)],
            [1, 2, ["refs/grill-me/v1", "refs/grill-me/v2"]])


def ceiling_is_never_reserved(base: str) -> tuple:
    root = repo(base)
    on_branch(root, "side", "specs/v8999-zulu/spec.md")
    done = call(root, "--topic", "Next")
    return ([done.returncode, done.stderr.strip(), reservations(root)],
            [1, "no free version below v9000, where running lists start", []])


def blocked_reservation_fails_at_once(base: str) -> tuple:
    root = repo(base)
    git(root, "update-ref", "refs/grill-me/v1/stray", "HEAD")
    start = time.monotonic()
    done = call(root, "--topic", "Next")
    quick = time.monotonic() - start < 3  # a lock wait would spend 5 seconds retrying
    return ([done.returncode, "'refs/grill-me/v1/stray' exists" in done.stderr, quick], [1, True, True])


def main_checkout_never_claims_a_version(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v006-papa/spec.md")
    git(root, "switch", "-q", "-c", "release/v2")
    got = run(root, "--topic", "Quebec")
    return [got["version"], got["source"]], [7, "next"]


def branch_name_owns_version(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v001-alpha/spec.md")
    got = run(worktree(root, "worktree/v7"), "--topic", "Fast Lane")
    return ([got["version"], got["source"], got["spec"], got["problem"], reservations(root)],
            [7, "branch", "specs/v007-fast-lane/spec.md", None, []])


def padded_branch_name_owns_version(base: str) -> tuple:
    got = run(worktree(repo(base), "worktree/v007"), "--topic", "Padded")
    return [got["version"], got["folder"]], [7, "specs/v007-padded"]


def worktree_folder_owns_version(base: str) -> tuple:
    root = repo(base)
    got = run(worktree(root, "scratch", "v126"), "--topic", "Romeo")
    return [got["version"], got["source"], got["spec"], got["problem"]], [126, "folder", "specs/v126-romeo/spec.md", None]


def existing_pair_is_reused(base: str) -> tuple:
    root = repo(base)
    tree = worktree(root, "worktree/v8")
    write(tree, "specs/v008-echo/spec.md", "specs/v008-echo/plan.md")
    got = run(tree, "--topic", "Another Name")
    return ([got["spec"], got["plan"], got["problem"]],
            ["specs/v008-echo/spec.md", "specs/v008-echo/plan.md", None])


def half_pair_gets_its_missing_file(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v004-sierra/spec.md")
    got = run(root, "--version", "4")
    return [got["plan"], got["problem"]], ["specs/v004-sierra/plan.md", None]


def version_used_elsewhere_collides(base: str) -> tuple:
    root = repo(base)
    on_branch(root, "side", "specs/v009-foxtrot/spec.md")
    got = run(worktree(root, "worktree/v9"), "--topic", "Golf")
    return got["problem"], "v9 is already held by: specs/v009-foxtrot"


def reserved_version_collides(base: str) -> tuple:
    root = repo(base)
    run(root, "--topic", "Sierra")
    got = run(worktree(root, "worktree/v1"), "--topic", "Tango")
    return got["problem"], "v1 is already held by: refs/grill-me/v1"


def same_last_segment_collides(base: str) -> tuple:
    root = repo(base)
    git(root, "branch", "team/v3")
    got = run(worktree(root, "worktree/v3"), "--topic", "Uniform")
    return got["problem"], "v3 is already held by: refs/heads/team/v3"


def pruned_worktree_folder_holds_nothing(base: str) -> tuple:
    root = repo(base)
    stale = worktree(root, "side", folder="v9")
    subprocess.run(["rm", "-rf", stale], check=True)
    return run(worktree(root, "worktree/v9"), "--topic", "Sierra")["problem"], None


def merged_own_pair_is_not_a_clash(base: str) -> tuple:
    root = repo(base)
    tree = worktree(root, "worktree/v3")
    write(tree, "specs/v003-kilo/spec.md", "specs/v003-kilo/plan.md")
    git(root, "merge", "-q", "--no-ff", "-m", "merge", "worktree/v3")
    return run(tree, "--topic", "Kilo")["problem"], None


def given_version_revises_its_pair(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v003-victor/spec.md", "specs/v003-victor/plan.md")
    got = run(root, "--version", "3")
    return ([got["spec"], got["plan"], got["source"], got["problem"], reservations(root)],
            ["specs/v003-victor/spec.md", "specs/v003-victor/plan.md", "given", None, []])


def given_version_without_pair_is_a_problem(base: str) -> tuple:
    got = run(repo(base), "--version", "4")
    return got["problem"], "v4 has no spec folder yet; pass --topic to name a new one"


def duplicate_folders_are_a_problem(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v002-whiskey/spec.md", "specs/v002-xray/spec.md")
    got = run(root, "--version", "2")
    return got["problem"], "several folders hold v2: specs/v002-whiskey, specs/v002-xray"


def unsafe_folder_name_is_a_problem(base: str) -> tuple:
    root = repo(base)
    write(root, "specs/v1-$(touch pwned)/spec.md")
    got = run(root, "--version", "1")
    return ([got["problem"], got["spec"]],
            ["spec folder names may hold only a-z, 0-9 and dashes after the version: specs/v1-$(touch pwned)", None])


def symlinked_file_is_a_problem(base: str) -> tuple:
    root = repo(base)
    tree = worktree(root, "worktree/v5")
    write(tree, "specs/v005-november/spec.md")
    os.symlink(os.path.join(base, "outside.md"), os.path.join(tree, "specs/v005-november/plan.md"))
    return (run(tree, "--topic", "November")["problem"],
            "spec folders and files must not be symlinks: specs/v005-november/plan.md")


def symlinked_folder_is_a_problem(base: str) -> tuple:
    root = repo(base)
    os.makedirs(os.path.join(base, "elsewhere"))
    os.makedirs(os.path.join(root, "specs"))
    os.symlink(os.path.join(base, "elsewhere"), os.path.join(root, "specs/v002-oscar"))
    return (run(root, "--version", "2")["problem"],
            "spec folders and files must not be symlinks: specs/v002-oscar")


def folder_outside_or_at_root_is_refused(base: str) -> tuple:
    root = repo(base)
    os.symlink(base, os.path.join(root, "escape"))
    folders = ("../elsewhere", "/tmp/elsewhere", "escape/specs", ".", "a/..")
    errors = [call(root, "--dir", folder, "--topic", "Oscar").stderr.strip() for folder in folders]
    return errors, [f"{folder} must be a folder below the repository root" for folder in folders]


def empty_topic_is_refused_before_reserving(base: str) -> tuple:
    root = repo(base)
    done = call(root, "--topic", "!!!")
    return ([done.returncode, done.stderr.strip(), reservations(root)],
            [1, "the topic needs at least one letter or digit from a-z or 0-9", []])


def topic_is_cut_to_six_words(base: str) -> tuple:
    got = run(repo(base), "--topic", "one two three four five six seven")
    return got["folder"], "specs/v001-one-two-three-four-five-six"


def custom_folder_is_normalized(base: str) -> tuple:
    root = repo(base)
    write(root, "design/specs/v006-hotel/spec.md")
    got = run(root, "--dir", "design/specs/", "--topic", "India")
    return [got["version"], got["plan"]], [7, "design/specs/v007-india/plan.md"]


def subfolder_run_gives_root_paths(base: str) -> tuple:
    root = repo(base)
    os.makedirs(os.path.join(root, "src", "deep"))
    return run(os.path.join(root, "src", "deep"), "--topic", "Juliet")["spec"], "specs/v001-juliet/spec.md"


CASES = [
    empty_repo_starts_at_one,
    running_lists_never_count,
    unpadded_folders_count,
    other_branches_count,
    non_ascii_folder_on_branch_counts,
    uncommitted_folder_counts,
    reserved_branch_is_skipped,
    each_run_reserves_a_new_version,
    ceiling_is_never_reserved,
    blocked_reservation_fails_at_once,
    main_checkout_never_claims_a_version,
    branch_name_owns_version,
    padded_branch_name_owns_version,
    worktree_folder_owns_version,
    existing_pair_is_reused,
    half_pair_gets_its_missing_file,
    version_used_elsewhere_collides,
    reserved_version_collides,
    same_last_segment_collides,
    pruned_worktree_folder_holds_nothing,
    merged_own_pair_is_not_a_clash,
    given_version_revises_its_pair,
    given_version_without_pair_is_a_problem,
    duplicate_folders_are_a_problem,
    unsafe_folder_name_is_a_problem,
    symlinked_file_is_a_problem,
    symlinked_folder_is_a_problem,
    folder_outside_or_at_root_is_refused,
    empty_topic_is_refused_before_reserving,
    topic_is_cut_to_six_words,
    custom_folder_is_normalized,
    subfolder_run_gives_root_paths,
]


def check(case) -> str | None:
    """Run one case in its own temporary folder; the failure text, or None when it holds."""
    with tempfile.TemporaryDirectory() as base:
        try:
            got, want = case(os.path.realpath(base))
        except (AssertionError, ValueError, subprocess.CalledProcessError) as error:
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
    print(f"ok: {len(CASES)} version rules hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
