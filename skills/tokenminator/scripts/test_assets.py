#!/usr/bin/env python3
"""Self-test for the templates under assets/.

Purpose: prove the files a playbook tells an agent to copy work as shipped: the check
runner, the AGENTS.md path test, and the outline tool. A repository that copied one can
also prove its copy is still the shipped file.
The four templates: check, test_agents_md.py, outline, read_guard.py.
Usage: python3 scripts/test_assets.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
COPIES = {
    "check": "scripts/check", "outline": "scripts/outline",
    "test_agents_md.py": "scripts/test_agents_md.py", "read_guard.py": "scripts/read_guard.py",
}


def write(root: str, relative: str, text: str) -> None:
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as target:
        target.write(text)


def call(root: str, *command: str) -> tuple[int, str]:
    done = subprocess.run(command, cwd=root, capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def project(root: str, checks: list, inert: list | None = None) -> None:
    for name in COPIES:
        os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
        shutil.copy(os.path.join(ASSETS, name), os.path.join(root, "scripts", name))
    write(root, "scripts/checks.json", json.dumps({"requires": ["git"], "inert": inert or [], "checks": checks}))


def runner_cases() -> list[str]:
    failures: list[str] = []
    passing = {"id": "pass", "cmd": [sys.executable, "-c", "print('noise ' * 500)"], "paths": ["src/*"]}
    lint = {"id": "lint", "parse": "located", "paths": ["docs/*"],
            "cmd": [sys.executable, "-c", "import sys; print('docs/a.md:7: WORD banned word'); sys.exit(1)"]}
    unit = {"id": "unit", "parse": "pytest", "paths": ["tests/*"],
            "cmd": [sys.executable, "-c", "import sys; print('FAILED tests/test_a.py::test_x - assert 1 == 2'); sys.exit(1)"],
            "fix": [sys.executable, "-c", "print('formatted')"]}
    with tempfile.TemporaryDirectory() as root:
        project(root, [passing])
        status, out = call(root, "scripts/check", "--full")
        if status != 0 or len(out.splitlines()) != 1 or not out.startswith("[PASS] pass "):
            failures.append(f"runner: a passing run is one line per check and nothing else, got {status}:\n{out}")
        with open(os.path.join(root, ".check/summary.json"), encoding="utf-8") as source:
            summary = json.load(source)
        if summary["checks"][0]["logBytes"] < 2000 or not os.path.isfile(os.path.join(root, summary["checks"][0]["log"])):
            failures.append("runner: tool output belongs in a log file whose size the summary records")

        project(root, [passing, lint, unit])
        status, out = call(root, "scripts/check", "--full")
        expected = ("[FAIL] lint", "docs/a.md:7: WORD banned word", "[FAIL] unit", "tests/test_a.py:0: test_x - assert 1 == 2")
        if status != 1 or not all(text in out for text in expected) or "[PASS] pass" not in out:
            failures.append(f"runner: each failed check should report alone, with its finding inline, got {status}:\n{out}")
        status, out = call(root, "scripts/check", "fix")
        if status != 0 or out.split()[:2] != ["[FIXED]", "unit"] or len(out.splitlines()) != 1:
            failures.append(f"runner: fix mode runs only the checks that define a fix, got {status}:\n{out}")

        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "start"]):
            call(root, *command)
        write(root, "docs/b.md", "new\n")
        status, out = call(root, "scripts/check", "--impacted")
        if "[FAIL] lint" not in out or "pass" in out or "unit" in out:
            failures.append(f"runner: --impacted should run only what the changed paths trigger, got:\n{out}")
        write(root, "unknown/file.bin", "x\n")
        status, out = call(root, "scripts/check", "--impacted")
        if "unrecognized path 'unknown/file.bin'" not in out or "[PASS] pass" not in out:
            failures.append(f"runner: an unclassified path should run everything and say why, got:\n{out}")

        write(root, "scripts/checks.json", "{broken")
        status, out = call(root, "scripts/check")
        if status != 2 or "[ENV]" not in out:
            failures.append(f"runner: a broken config is an environment problem, exit 2, got {status}:\n{out}")
        project(root, [passing])
        write(root, "scripts/checks.json", json.dumps({"requires": ["no-such-tool-xyz"], "checks": [passing]}))
        status, out = call(root, "scripts/check", "doctor")
        if status != 2 or "no-such-tool-xyz" not in out:
            failures.append(f"runner: doctor should name a missing tool and exit 2, got {status}:\n{out}")
    return failures


def path_test_cases() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as root:
        project(root, [{"id": "x", "cmd": ["true"]}])
        call(root, "git", "init", "-q")
        write(root, ".gitignore", "runtime/\n")
        block = "<!-- BEGIN:tokenminator-rules v3 | note -->\n`not/a/path.py`\n<!-- END:tokenminator-rules -->\n"
        write(root, "AGENTS.md", f"# P\n\n{block}\n## Where Things Live\n\n`scripts/check`, `runtime/`\n")
        status, out = call(root, sys.executable, "scripts/test_agents_md.py")
        if status != 0 or "ok: 2 paths" not in out:
            failures.append(f"path test: real and git-ignored paths pass, the rules block is cut out, got {status}:\n{out}")
        write(root, "AGENTS.md", "# P\n\n## Where Things Live\n\n`scripts/gone.py`\n")
        status, out = call(root, sys.executable, "scripts/test_agents_md.py")
        if status != 1 or "scripts/gone.py" not in out:
            failures.append(f"path test: a dead path should fail by name, got {status}:\n{out}")
        write(root, "AGENTS.md", "# P\n\nNo paths here.\n")
        status, out = call(root, sys.executable, "scripts/test_agents_md.py")
        if status != 1:
            failures.append("path test: a file that names no path must not pass")
    return failures


def outline_cases() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as root:
        project(root, [{"id": "x", "cmd": ["true"]}])
        write(root, "big.py", "LIMIT = 3\n\n\nclass Audit:\n    def run(self):\n        x = 1\n        return x\n\n\ndef main():\n    pass\n")
        status, out = call(root, "scripts/outline", "big.py")
        if status != 0 or out.splitlines() != ["1: LIMIT = 3", "4: class Audit:", "5:     def run(self):", "10: def main():"]:
            failures.append(f"outline: expected constants, classes, and functions with line numbers, got:\n{out}")
        status, out = call(root, "scripts/outline", "big.py", "--grep", "main")
        if out.splitlines() != ["10: def main():"]:
            failures.append(f"outline: --grep should keep matching rows only, got:\n{out}")
    return failures


def read_guard_cases() -> list[str]:
    failures: list[str] = []

    def guard(root: str, event: object, **env: str) -> tuple[int, str]:
        done = subprocess.run(
            [os.path.join(root, "scripts/read_guard.py")], input=event if isinstance(event, str) else json.dumps(event),
            capture_output=True, text=True, env={**os.environ, **env},
        )
        return done.returncode, done.stdout

    with tempfile.TemporaryDirectory() as root:
        project(root, [{"id": "x", "cmd": ["true"]}])
        write(root, "big.py", "x = 1\n" * 2000)
        write(root, "big.png", "x" * 9000)
        write(root, "small.py", "x = 1\n")
        big = os.path.join(root, "big.py")
        status, out = guard(root, {"tool_name": "Read", "tool_input": {"file_path": big}}, READ_GUARD_BYTES="5000")
        decision = json.loads(out)["hookSpecificOutput"] if out.strip() else {}
        if status != 0 or decision.get("permissionDecision") != "deny" or "offset and limit" not in decision.get("permissionDecisionReason", ""):
            failures.append(f"read guard: a whole read of a large file should be denied with the cheaper way, got {status} {out!r}")
        allowed = [
            {"tool_name": "Read", "tool_input": {"file_path": big, "offset": 1, "limit": 50}},
            {"tool_name": "Read", "tool_input": {"file_path": os.path.join(root, "big.png")}},
            {"tool_name": "Read", "tool_input": {"file_path": os.path.join(root, "small.py")}},
            {"tool_name": "Read", "tool_input": {"file_path": os.path.join(root, "missing.py")}},
            {"tool_name": "Bash", "tool_input": {"command": "ls"}},
            "not json",
        ]
        for event in allowed:
            status, out = guard(root, event, READ_GUARD_BYTES="5000")
            if status != 0 or out.strip():
                failures.append(f"read guard: should pass silently and fail open, got {status} {out!r} for {event}")
    return failures


def parity_cases() -> list[str]:
    """In a repository that copied a template, the copy must still be the shipped file."""
    failures: list[str] = []
    done = subprocess.run(["git", "-C", HERE, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if done.returncode != 0:
        return failures
    for name, relative in COPIES.items():
        copy = os.path.join(done.stdout.strip(), relative)
        if os.path.isfile(copy) and os.path.realpath(copy) != os.path.realpath(os.path.join(ASSETS, name)):
            with open(copy, "rb") as mine, open(os.path.join(ASSETS, name), "rb") as shipped:
                if mine.read() != shipped.read():
                    failures.append(f"parity: {relative} differs from assets/{name}; copy the template again, never edit the copy")
    return failures


def main() -> int:
    failures = runner_cases() + path_test_cases() + outline_cases() + read_guard_cases() + parity_cases()
    if failures:
        print("\n\n".join(failures))
        print(f"\nFAILED: {len(failures)} problem(s)")
        return 1
    print("ok: the check runner, the AGENTS.md path test, the outline tool, and the read guard work as shipped, and local copies match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
