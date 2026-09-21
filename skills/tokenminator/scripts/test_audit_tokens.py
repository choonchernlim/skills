#!/usr/bin/env python3
"""Fixture self-test for audit_tokens.py.

Purpose: prove the audit accepts the good fixture and raises the expected codes
for every bad case, so a rule change cannot silently disable a check, and prove
the two mutations (--fix-rules-block and --fix) are safe to run repeatedly.
Usage: python3 scripts/test_audit_tokens.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, "audit_tokens.py")
GOOD = os.path.join(HERE, "fixtures", "good")
BAD = os.path.join(HERE, "fixtures", "bad")
REFERENCES = os.path.join(os.path.dirname(HERE), "references")
TODAY = "2026-09-19"

# Fixture lockfiles are tiny stubs, so these cases drop the size floor.
SMALL = ["--limit", "small=0"]

# case: (extra arguments, codes the case must raise)
EXPECTED: dict[str, tuple[list[str], set[str]]] = {
    "bare": (SMALL, {"AGT-MISSING", "CLD-IMPORT", "RUN-ENTRY", "DENY-MISSING"}),
    "instructions": (
        ["--limit", "ins=300", *SMALL],
        {"RULES-MISSING", "ORIENT-MISSING", "DNR-MISSING", "PATH-DEAD", "CLD-FORK", "CLD-RULE",
         "CLD-COMPACT", "INS-LONG"},
    ),
    "rules-outdated": ([], {"RULES-OUTDATED"}),
    "rules-legacy": ([], {"RULES-OUTDATED"}),
    "rules-edited": ([], {"RULES-EDITED"}),
    "rules-malformed": ([], {"RULES-EDITED"}),
    "skills": (
        ["--limit", "rootchars=50", "--limit", "desc=40"],
        {"SKILL-DUP", "SKILL-LINK", "SKILL-BUDGET", "SKILL-DESC"},
    ),
    "deny": (SMALL, {"DENY-DEAD", "DENY-SEARCH", "DNR-UNLISTED", "CFG-PARSE"}),
    "caps": (["--limit", "source=100"], {"CFG-CAP", "SRC-LARGE"}),
    "runner": ([], {"RUN-UNDOC", "RUN-NOSUMMARY", "RUN-NOISY", "CI-DUP"}),
    "hooks-one": ([], {"HOOK-ONE", "HOOK-HOME"}),
    "hooks-diff": ([], {"HOOK-DIFF"}),
    "e2e": (
        [],
        {"MCP-BROWSER", "PW-REPORTER", "PW-RETRIES", "PW-SLEEP", "PW-SERVER", "PW-REUSE",
         "PW-MEDIA", "PW-TRACE"},
    ),
    "terraform": ([], {"TF-NOTEST", "TF-NOLINT"}),
}
FIXABLE = ("instructions", "rules-outdated", "rules-legacy", "rules-edited")
STALE_CODE = "FACT-STALE"
HOME = [""]  # the home folder `run` hands to the audit; set in main
EM_DASH = chr(0x2014)  # built from its code point so this file stays free of it


def run(*arguments: str) -> tuple[int, str, str]:
    # Every run gets an empty home folder unless a case supplies one, so the
    # result never depends on the machine's real user-level config.
    done = subprocess.run(
        [sys.executable, AUDIT, *arguments], capture_output=True, text=True,
        env={**os.environ, "HOME": HOME[0]},
    )
    return done.returncode, done.stdout, done.stderr


def snapshot(root: str) -> dict[str, tuple]:
    """Path -> (link target or content hash) for everything under a folder."""
    state = {}
    for base, directories, names in os.walk(root):
        for name in directories + names:
            path = os.path.join(base, name)
            if os.path.islink(path):
                state[path] = ("link", os.readlink(path))
            elif os.path.isfile(path):
                with open(path, "rb") as source:
                    state[path] = ("file", hashlib.sha256(source.read()).hexdigest())
    return state


def codes(root: str, *extra: str) -> tuple[int, set[str]]:
    status, out, err = run(root, "--format", "json", "--today", TODAY, *extra)
    if status == 2:
        raise AssertionError(f"audit could not run on {root}: {err}")
    return status, {finding["code"] for finding in json.loads(out)["findings"]}


def outside_block(text: str) -> str:
    # Both names: a legacy block is outside the text the fix must preserve, same as a current one.
    return re.sub(r"<!-- BEGIN:(?:tokenminator|saving-private-tokens)-rules v\d+(?: \|[^>\n]*)? -->.*?<!-- END:(?:tokenminator|saving-private-tokens)-rules -->\n?", "", text, flags=re.S)


def write(root: str, relative: str, text: str) -> None:
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as target:
        target.write(text)


def claude_layer(root: str) -> None:
    """The bridge, the compaction note, and the output caps that a clean repository carries."""
    write(root, "CLAUDE.md", "@AGENTS.md\n\n## Compact Instructions\n\nKeep the plan and the failing check ids.\n")
    write(root, ".claude/settings.json", '{"bashOutputMaxChars": 10000}\n')
    write(root, ".codex/config.toml", "tool_output_token_limit = 2500\n")


def findings(root: str, *extra: str) -> dict[str, dict]:
    _, out, _ = run(root, "--format", "json", "--today", TODAY, *extra)
    return {finding["code"]: finding for finding in json.loads(out)["findings"]}


def user_cases() -> tuple[list[str], set[str]]:
    """The user scope reads a home folder, names the real owner, and never writes."""
    failures: list[str] = []
    raised: set[str] = set()
    empty = HOME[0]
    with tempfile.TemporaryDirectory() as scratch:
        home, owner, other = (os.path.join(scratch, name) for name in ("home", "owner", "other"))
        # `owner` is a dotfiles-style repository: the home folder links into it.
        write(owner, ".git/HEAD", "ref: refs/heads/main\n")
        write(owner, "AGENTS.md", "# Owner\n\n## Where Things Live\n\n`policy.md`\n")
        claude_layer(owner)
        write(owner, "policy.md", "rule\n" * 40)
        write(owner, "skills/long/SKILL.md", "---\nname: long\ndescription: " + "word " * 30 + "\n---\n")
        write(other, "AGENTS.md", "# Other\n\n## Where Things Live\n\n`AGENTS.md`\n")
        claude_layer(other)
        os.makedirs(os.path.join(home, ".claude"))
        os.makedirs(os.path.join(home, ".codex"))
        os.symlink(os.path.join(owner, "policy.md"), os.path.join(home, ".claude", "CLAUDE.md"))
        os.symlink(os.path.join(owner, "policy.md"), os.path.join(home, ".codex", "AGENTS.md"))
        os.symlink(os.path.join(owner, "skills"), os.path.join(home, ".claude", "skills"))
        write(home, ".claude.json", '{"mcpServers": {"demo": {"env": {"TOKEN": "secret"}}}}')
        # Codex loads every tool of a server that lists none, so that server is a finding.
        with open(os.path.join(owner, ".codex", "config.toml"), "a", encoding="utf-8") as target:
            target.write('\n[mcp_servers.heavy]\ncommand = "heavy"\n\n[mcp_servers.lean]\ncommand = "lean"\nenabled_tools = ["one", "two"]\n')
        os.symlink(os.path.join(owner, ".codex", "config.toml"), os.path.join(home, ".codex", "config.toml"))
        for root in (owner, other):
            run(root, "--fix-rules-block")
        limits = ["--limit", "ins=100", "--limit", "userchars=50", "--limit", "desc=40"]
        HOME[0] = home
        try:
            before = snapshot(scratch)
            inside = findings(owner, *limits)
            status_inside, out, _ = run(owner, "--format", "json", *limits)
            outside = findings(other, *limits)
            status_outside, _, _ = run(other, *limits)
            _, human, _ = run(other, "--user", *limits)
            status_mixed, _, _ = run(other, "--user", "--fix-rules-block")
            after = snapshot(scratch)
        finally:
            HOME[0] = empty
        expected = {"USR-INS", "USR-SKILL-BUDGET", "USR-SKILL-DESC", "USR-MCP"}
        raised = set(inside) & expected
        if raised != expected:
            failures.append(f"user scope: expected {sorted(expected)}, got {sorted(inside)}")
        elif not all(inside[code]["fixable"] and inside[code]["owner"] == "this repository" for code in expected):
            failures.append("user scope: findings that resolve into the audited repository should be fixable there")
        if status_inside != 1:
            failures.append(f"user scope: a fixable user finding should fail the audit, got exit {status_inside}")
        if any(outside[code]["fixable"] or not outside[code]["owner"].endswith("owner") for code in expected & set(outside)):
            failures.append("user scope: from another repository the findings should be proposals that name the owner")
        if status_outside != 0:
            failures.append(f"user scope: proposals must not fail another repository's audit, got exit {status_outside}")
        if json.loads(out)["userScope"]["baseline"][0]["what"].count("~/") != 2:
            failures.append("user scope: one shared instruction file should be priced once for both agents")
        if "secret" in human or "demo" not in human:
            failures.append("user scope: MCP servers should be listed by name only")
        scope = json.loads(out)["userScope"]
        agents = {row.get("agent"): row["tokens"] for row in scope["baseline"] if row.get("agent")}
        shared = sum(row["tokens"] for row in scope["baseline"] if not row.get("agent"))
        if set(agents) != {"claude", "codex"} or scope["baselineTokens"] != shared + max(agents.values()):
            failures.append(f"user scope: a session runs one agent, so the total counts the costlier one, got {scope}")
        heavy = inside.get("USR-MCP", {}).get("message", "")
        if "heavy" not in heavy or "lean" in heavy:
            failures.append(f"user scope: only the Codex server with no `enabled_tools` is a finding, got {heavy!r}")
        if status_mixed != 2:
            failures.append("user scope: --user with --fix-rules-block should exit 2")
        if before != after:
            failures.append("user scope: the audit changed files; it must only read")
    return failures, raised


def composed_cases() -> list[str]:
    """Behaviour that depends on what a repository contains, built in scratch folders."""
    failures: list[str] = []

    # The one write follows a link inside the repository and refuses one that leaves it.
    with tempfile.TemporaryDirectory() as scratch:
        work, elsewhere = os.path.join(scratch, "work"), os.path.join(scratch, "elsewhere.md")
        write(work, "docs/agents.md", "# Project\n")
        write(scratch, "elsewhere.md", "# Someone else's file\n")
        os.symlink("docs/agents.md", os.path.join(work, "AGENTS.md"))
        status, _, _ = run(work, "--fix-rules-block", "--no-user")
        with open(os.path.join(work, "docs", "agents.md"), encoding="utf-8") as source:
            if status == 2 or not os.path.islink(os.path.join(work, "AGENTS.md")) or "Token Discipline" not in source.read():
                failures.append("guarded write: a link inside the repository should survive and its target be updated")
        os.remove(os.path.join(work, "AGENTS.md"))
        os.symlink(elsewhere, os.path.join(work, "AGENTS.md"))
        status, _, _ = run(work, "--fix-rules-block", "--no-user")
        with open(elsewhere, encoding="utf-8") as source:
            if status != 2 or "Token Discipline" in source.read():
                failures.append("guarded write: a target outside the repository must be refused and left untouched")

    # A nix repository that ships a skill: the skill's tests are not the project's
    # tests, `nix flake check` is the entry point, and the block carries no browser rules.
    with tempfile.TemporaryDirectory() as scratch:
        write(scratch, "flake.nix", "{ outputs = _: { checks = { }; }; }\n")
        write(scratch, "flake.lock", "{}\n")
        write(scratch, "AGENTS.md", "# Project\n\nRun `nix flake check`.\n\n## Where Things Live\n\n`flake.nix`\n")
        claude_layer(scratch)
        write(scratch, "home/skills/demo/SKILL.md", "---\nname: demo\ndescription: demo\n---\n")
        write(scratch, "home/skills/demo/scripts/test_demo.py", "def test(): pass\n")
        run(scratch, "--fix-rules-block")
        found = findings(scratch)
        if found:
            failures.append(f"nix repo: expected no findings, got {sorted(found)}")
        _, block, _ = run(scratch, "--print-rules-block")
        if "Playwright" in block or "browser MCP" in block or "uv tree" in block:
            failures.append("nix repo: the rules block carries rules for stacks the repository lacks")
        if "`nix flake metadata`" not in block:
            failures.append("nix repo: the rules block lacks the nix package-manager hint")

    # An ignore file under the former skill name is still honoured, with a notice to rename
    # it, so existing ignores do not silently lapse. The audit never moves the file itself.
    with tempfile.TemporaryDirectory() as scratch:
        write(scratch, "AGENTS.md", "# Project\n\n## Where Things Live\n\nNothing yet.\n")
        write(scratch, "CLAUDE.md", "@AGENTS.md\n")
        if "RULES-MISSING" not in findings(scratch):
            failures.append("ignore file: the probe repository should raise RULES-MISSING")
        write(scratch, ".agents/saving-private-tokens.json", '{"ignore": {"RULES-MISSING": "probe"}}\n')
        _, _, notice = run(scratch, "--format", "json", "--today", TODAY)
        if "RULES-MISSING" in findings(scratch) or ".agents/tokenminator.json" not in notice:
            failures.append("ignore file: the former name should still be honoured, with a rename notice")
        os.rename(os.path.join(scratch, ".agents/saving-private-tokens.json"), os.path.join(scratch, ".agents/tokenminator.json"))
        _, _, notice = run(scratch, "--format", "json", "--today", TODAY)
        if "RULES-MISSING" in findings(scratch) or notice:
            failures.append("ignore file: the current name should be honoured without a notice")

    # The managed block does not count against the budget, and --sections shows why.
    with tempfile.TemporaryDirectory() as scratch:
        write(scratch, "AGENTS.md", "# Project\n\n## Where Things Live\n\n" + "word " * 40 + "\n")
        write(scratch, "CLAUDE.md", "@AGENTS.md\n")
        size = os.path.getsize(os.path.join(scratch, "AGENTS.md"))
        limit = ["--limit", f"ins={size + 10}"]
        run(scratch, "--fix-rules-block")
        if "INS-LONG" in findings(scratch, *limit):
            failures.append("budget: installing the managed block pushed the file over budget")
        _, sections, _ = run(scratch, "--sections", *limit)
        if "managed rules block, not counted" not in sections or "## Where Things Live" not in sections:
            failures.append("sections: expected a row per heading and one for the managed block")

    # One costly file, both guard layers missing: the two findings sum to its cost, not double.
    with tempfile.TemporaryDirectory() as scratch:
        write(scratch, "AGENTS.md", "# Project\n\n## Where Things Live\n\n`uv.lock`\n")
        write(scratch, "CLAUDE.md", "@AGENTS.md\n")
        write(scratch, "uv.lock", "x" * 40000)
        found = findings(scratch)
        layers = [found.get("DENY-MISSING"), found.get("DNR-MISSING")]
        if not all(layers):
            failures.append(f"estimates: expected both guard findings, got {sorted(found)}")
        elif sum(layer["before"] for layer in layers) != 40000 // 4 * 3 or not all(layer["measured"] for layer in layers):
            failures.append(f"estimates: guard layers should be measured and sum to one file's cost, got {layers}")

    # One finding per agent and per unscoped rule file: a cap set inside a TOML table
    # is not a cap, and a rule file with `paths:` loads on demand, so it is left alone.
    _, out, _ = run(os.path.join(BAD, "caps"), "--format", "json", "--today", TODAY)
    capped = sorted(f["path"] for f in json.loads(out)["findings"] if f["code"] == "CFG-CAP")
    if capped != [".claude/settings.json", ".codex/config.toml"]:
        failures.append(f"caps: expected one CFG-CAP per agent config, got {capped}")
    _, out, _ = run(os.path.join(BAD, "instructions"), "--format", "json", "--today", TODAY)
    ruled = [f["path"] for f in json.loads(out)["findings"] if f["code"] == "CLD-RULE"]
    if ruled != [".claude/rules/style.md"]:
        failures.append(f"rule files: only the unscoped file should be flagged, got {ruled}")

    # `next` names one area: worst severity first, the check runner before hooks,
    # and nothing at all once only proposals remain.
    def following(root: str, *extra: str) -> object:
        _, out, _ = run(root, "--format", "json", "--today", TODAY, *extra)
        return json.loads(out)["next"]

    step = following(os.path.join(BAD, "bare"), *SMALL)
    if not step or step["area"] != "instruction-files":
        failures.append(f"next: a repository with no AGENTS.md should start with instruction files, got {step}")
    with tempfile.TemporaryDirectory() as scratch:
        shutil.copytree(os.path.join(BAD, "hooks-one"), os.path.join(scratch, "work"), symlinks=True)
        write(os.path.join(scratch, "work"), "tests/test_demo.py", "def test(): pass\n")
        write(os.path.join(scratch, "work"), "ruff.toml", "line-length = 100\n")
        step = following(os.path.join(scratch, "work"))
        if not step or step["area"] != "check-runner":
            failures.append(f"next: the check runner should come before hooks, got {step}")
    if following(GOOD) is not None:
        failures.append("next: a clean repository should have no next area")

    # A folder-only ignore pattern covers a runtime folder that does not exist yet, so an
    # instruction may name it. A missing path that git does not ignore is still dead.
    with tempfile.TemporaryDirectory() as scratch:
        subprocess.run(["git", "init", "-q", scratch], check=True)
        write(scratch, ".gitignore", "work/cache/\n")
        write(scratch, "work/kept.txt", "kept\n")
        write(scratch, "AGENTS.md", "# Project\n\n## Where Things Live\n\n`work/kept.txt`, `work/cache/`, `work/gone/`\n")
        write(scratch, "CLAUDE.md", "@AGENTS.md\n")
        _, out, _ = run(scratch, "--format", "json", "--today", TODAY, "--no-user")
        dead = [f["message"] for f in json.loads(out)["findings"] if f["code"] == "PATH-DEAD"]
        if len(dead) != 1 or "work/gone/" not in dead[0]:
            failures.append(f"ignored folder: only the path git does not ignore is dead, got {dead}")

    # A skill collection: with no source outside the skills, the skills are the project,
    # so their tests count and the audit is stable before and after a root script appears.
    with tempfile.TemporaryDirectory() as scratch:
        write(scratch, "README.md", "# Skills\n")
        write(scratch, "skills/demo/SKILL.md", "---\nname: demo\ndescription: demo\n---\n")
        write(scratch, "skills/demo/scripts/test_demo.py", "def test(): pass\n")
        _, out, _ = run(scratch, "--format", "json", "--today", TODAY, "--no-user")
        result = json.loads(out)
        if "python" not in result["stacks"] or "RUN-ENTRY" not in {f["code"] for f in result["findings"]}:
            failures.append(f"skill collection: the skills are the project, got stacks {result['stacks']}")

    # The block names what the repository has: no entry line before an entry point exists,
    # the real command once it does, and no package-manager hint without its lockfile.
    with tempfile.TemporaryDirectory() as scratch:
        write(scratch, "AGENTS.md", "# Project\n")
        write(scratch, "app.py", "print('x')\n")
        _, block, _ = run(scratch, "--print-rules-block")
        if "Run checks with" in block or "uv tree" in block:
            failures.append("composed block: no entry line without an entry point, no hint without a lockfile")
        write(scratch, "tests/fixtures/sample/yarn.lock", "x\n")
        _, block, _ = run(scratch, "--print-rules-block")
        if "yarn list" in block:
            failures.append("composed block: a lockfile inside a test fixture is not the project's")
        write(scratch, "Makefile", "check:\n\tpython3 app.py\n")
        write(scratch, "uv.lock", "x\n")
        _, block, _ = run(scratch, "--print-rules-block")
        if "Run checks with `make check`" not in block or "`uv tree`" not in block:
            failures.append("composed block: expected the real entry point and the uv hint")
        if "managed by the tokenminator skill" not in block.splitlines()[0] or "- Managed by" in block:
            failures.append("composed block: the managed-by note belongs inside the begin marker")

    # The instruction budget follows the repository: the same file is over budget in a
    # small repository and within it in a large one. Its real cost is always reported.
    with tempfile.TemporaryDirectory() as scratch:
        write(scratch, "AGENTS.md", "# Project\n\n## Where Things Live\n\n" + "word " * 600 + "\n")
        write(scratch, "CLAUDE.md", "@AGENTS.md\n")
        expected = sum(os.path.getsize(os.path.join(scratch, name)) // 4 for name in ("AGENTS.md", "CLAUDE.md"))
        if "INS-LONG" not in findings(scratch):
            failures.append("scaled budget: a 3,000 byte file should be over budget in a two-file repository")
        for number in range(200):
            write(scratch, f"src/module_{number}.py", "x = 1\n")
        if "INS-LONG" in findings(scratch):
            failures.append("scaled budget: the same file should fit the budget of a 200-file repository")
        write(scratch, ".check/summary.json", '{"checks": [{"id": "a", "logBytes": 400}, {"id": "b", "logBytes": 40}]}\n')
        _, out, _ = run(scratch, "--format", "json", "--today", TODAY, "--no-user")
        measured = json.loads(out)["measured"]
        if measured.get("instructionFiles", {}).get("tokens") != expected:
            failures.append(f"measured: instruction files should be priced from their real size, got {measured}")
        if measured.get("lastCheckRun") != {"logTokens": 110, "checks": 2}:
            failures.append(f"measured: the last check run should be read from its summary, got {measured}")

    # The read guard is a Claude-only extra layer, so it never makes the two hook blocks differ.
    with tempfile.TemporaryDirectory() as scratch:
        work = os.path.join(scratch, "work")
        shutil.copytree(GOOD, work, symlinks=True)
        path = os.path.join(work, ".claude", "settings.json")
        with open(path, encoding="utf-8") as source:
            settings = json.load(source)
        settings.setdefault("hooks", {})["PreToolUse"] = [
            {"matcher": "Read", "hooks": [{"type": "command", "command": "scripts/read_guard.py"}]}
        ]
        write(work, ".claude/settings.json", json.dumps(settings))
        found = set(findings(work)) & {"HOOK-ONE", "HOOK-DIFF", "HOOK-HOME"}
        if found:
            failures.append(f"read guard: a Claude-only guard must not count as a hook difference, got {sorted(found)}")

    # --fix applies what needs no judgement, leaves the rest, repeats safely, and never
    # writes through a link that leaves the repository.
    with tempfile.TemporaryDirectory() as scratch:
        work, elsewhere = os.path.join(scratch, "work"), os.path.join(scratch, "elsewhere.json")
        write(work, "AGENTS.md", "# Project\n\n## Where Things Live\n\n`app.py`\n")
        write(work, "app.py", "print('x')\n")
        write(work, "package-lock.json", "{}\n")
        write(work, ".codex/config.toml", "model = \"x\"\n\n[mcp_servers.demo]\ntool_output_token_limit = 9\n")
        _, out, _ = run(work, "--fix", "--today", TODAY, *SMALL)
        left = set(findings(work, *SMALL))
        mechanical = {"CFG-CAP", "CLD-IMPORT", "CLD-COMPACT", "DENY-MISSING", "DENY-SEARCH", "RULES-MISSING"}
        if left & mechanical or "DNR-MISSING" not in left:
            failures.append(f"--fix: mechanical codes should clear and judgement codes stay, left {sorted(left)}:\n{out}")
        with open(os.path.join(work, ".codex/config.toml"), encoding="utf-8") as source:
            toml = source.read()
        if not toml.startswith("tool_output_token_limit = 2500\n") or "[mcp_servers.demo]\ntool_output_token_limit = 9" not in toml:
            failures.append(f"--fix: the Codex cap belongs above every table and the table is untouched, got {toml!r}")
        before = snapshot(work)
        _, again, _ = run(work, "--fix", "--today", TODAY, *SMALL)
        if snapshot(work) != before or "fixed nothing" not in again:
            failures.append(f"--fix: a second run should change nothing, got:\n{again}")
        os.remove(os.path.join(work, ".claude/settings.json"))
        write(scratch, "elsewhere.json", "{}\n")
        os.symlink(elsewhere, os.path.join(work, ".claude/settings.json"))
        _, out, _ = run(work, "--fix", "--today", TODAY, *SMALL)
        with open(elsewhere, encoding="utf-8") as source:
            if source.read() != "{}\n" or "skipped .claude/settings.json" not in out:
                failures.append(f"--fix: a settings file that links outside the repository must be refused, got:\n{out}")

    # A re-audit costs three lines, and once only low findings remain one run takes them all.
    with tempfile.TemporaryDirectory() as scratch:
        work = os.path.join(scratch, "work")
        shutil.copytree(os.path.join(BAD, "terraform"), work)
        write(work, "scripts/check", "#!/bin/sh\necho quiet > .check.log --quiet summary.json\n")
        write(work, "AGENTS.md", "# Project\n\nRun `scripts/check`.\n\n## Where Things Live\n\n`main.tf`\n")
        run(work, "--fix-rules-block", "--no-user")
        _, brief, _ = run(work, "--expect-cleared", "RULES-MISSING", "CFG-CAP", "--today", TODAY)
        lines = brief.splitlines()
        if len(lines) != 3 or lines[0] != "cleared: RULES-MISSING | NOT cleared: CFG-CAP" or not lines[1].startswith("open: "):
            failures.append(f"brief: expected three lines naming what cleared, got {lines}")
        step = following(work)
        if not step or set(step["areas"]) < {"context-diet", "infrastructure"} or "only low findings remain" not in lines[2]:
            failures.append(f"batching: low findings in several areas should share one run, got {step}")
    step = following(os.path.join(BAD, "bare"), *SMALL)
    if len(step["areas"]) != 1:
        failures.append(f"batching: a high finding still gets a run of its own, got {step}")

    # A missing AGENTS.md is priced as the exploring it replaces against the budget it may
    # spend, and a missing entry point by how many tools a check loop must rediscover.
    found = findings(os.path.join(BAD, "bare"), *SMALL)
    missing, entry = found["AGT-MISSING"], found["RUN-ENTRY"]
    if missing["measured"] or missing["after"] != 2000 // 4 or missing["before"] <= missing["after"]:
        failures.append(f"scaled estimates: AGT-MISSING should cost exploring, less the budget, got {missing}")
    if entry["before"] % (1500 * 4) or entry["before"] > 6000 * 4:
        failures.append(f"scaled estimates: RUN-ENTRY should scale with the check signals, got {entry}")

    return failures


def main() -> int:
    with tempfile.TemporaryDirectory() as empty_home:
        HOME[0] = empty_home
        return check()


def check() -> int:
    failures: list[str] = []

    # The second pass drops the size floor, so the fixture's stub lockfile counts as a
    # costly file and the deny rule, the Do Not Read entry, and `.ignore` must all cover it.
    for extra in ([], SMALL):
        status, found = codes(GOOD, *extra)
        if status != 0 or found:
            failures.append(f"good {extra}: expected exit 0 and no findings, got exit {status} {sorted(found)}")

    covered: set[str] = set()
    for case, (extra, expected) in EXPECTED.items():
        status, found = codes(os.path.join(BAD, case), *extra)
        covered |= expected
        if status != 1:
            failures.append(f"{case}: expected exit 1, got {status}")
        missing = expected - found
        if missing:
            failures.append(f"{case}: did not raise {sorted(missing)}; raised {sorted(found)}")
    on_disk = {name for name in os.listdir(BAD) if os.path.isdir(os.path.join(BAD, name))}
    if on_disk != set(EXPECTED):
        failures.append(f"bad cases on disk and in EXPECTED differ: {sorted(on_disk ^ set(EXPECTED))}")

    status, out, _ = run(GOOD, "--format", "json", "--today", "2099-01-01")
    stale = {finding["code"] for finding in json.loads(out)["findings"]}
    if stale != {STALE_CODE} or status != 0:
        failures.append(f"stale facts: expected only {STALE_CODE} as a note with exit 0, got exit {status} {sorted(stale)}")
    covered.add(STALE_CODE)

    user_failures, user_codes = user_cases()
    failures += user_failures
    covered |= user_codes

    _, listing, _ = run("--list-codes")
    declared = {line.split()[0] for line in listing.splitlines() if line.strip()}
    if declared != covered:
        failures.append(f"codes without a fixture, or fixtures for unknown codes: {sorted(declared ^ covered)}")

    for case in FIXABLE:
        with tempfile.TemporaryDirectory() as scratch:
            work = os.path.join(scratch, case)
            shutil.copytree(os.path.join(BAD, case), work, symlinks=True)
            _, block, _ = run(work, "--print-rules-block")
            agents = os.path.join(work, "AGENTS.md")
            with open(agents, encoding="utf-8") as source:
                before = source.read()
            first, _, err = run(work, "--fix-rules-block", "--format", "json", "--today", TODAY, *EXPECTED[case][0])
            if first == 2:
                failures.append(f"{case}: --fix-rules-block could not run: {err}")
                continue
            with open(agents, encoding="utf-8") as source:
                after = source.read()
            run(work, "--fix-rules-block", "--format", "json", "--today", TODAY)
            with open(agents, encoding="utf-8") as source:
                again = source.read()
            _, remaining = codes(work, *EXPECTED[case][0])
            if remaining & {"RULES-MISSING", "RULES-OUTDATED", "RULES-EDITED"}:
                failures.append(f"{case}: a RULES code survived the fix: {sorted(remaining)}")
            if block not in after:
                failures.append(f"{case}: the fixed file does not contain the managed block verbatim")
            if after.count("<!-- BEGIN:") != 1 or "saving-private-tokens" in after:
                failures.append(f"{case}: the fixed file must hold exactly one block, under the current name")
            if after != again:
                failures.append(f"{case}: a second fix changed the file; the fix is not idempotent")
            if outside_block(before).split() != outside_block(after).split():
                failures.append(f"{case}: text outside the markers changed")

    with tempfile.TemporaryDirectory() as scratch:
        work = os.path.join(scratch, "rules-malformed")
        shutil.copytree(os.path.join(BAD, "rules-malformed"), work)
        with open(os.path.join(work, "AGENTS.md"), encoding="utf-8") as source:
            before = source.read()
        status, _, _ = run(work, "--fix-rules-block")
        with open(os.path.join(work, "AGENTS.md"), encoding="utf-8") as source:
            after = source.read()
        if status != 2 or before != after:
            failures.append("rules-malformed: expected exit 2 and an untouched file")

    with tempfile.TemporaryDirectory() as scratch:
        status, _, _ = run(scratch, "--fix-rules-block")
        if status != 2:
            failures.append("fix without AGENTS.md: expected exit 2")
        status, _, _ = run(os.path.join(scratch, "missing"))
        if status != 2:
            failures.append("missing root: expected exit 2")

    _, full, _ = run("--print-rules-block", "full")
    reference = os.path.join(REFERENCES, "instruction-files.md")
    with open(reference, encoding="utf-8") as source:
        if full not in source.read():
            failures.append("references/instruction-files.md does not show the full managed block verbatim")

    failures += composed_cases()

    stamped = 0
    for name in sorted(os.listdir(REFERENCES)):
        with open(os.path.join(REFERENCES, name), encoding="utf-8") as source:
            for number, line in enumerate(source, start=1):
                if re.match(r"\|\s*[A-Z]{2}-\d{2}\s*\|", line):
                    stamped += 1
                    if not re.search(r"\|\s*\d{4}-\d{2}-\d{2}\s*\|", line):
                        failures.append(f"{name}:{number}: fact row has no YYYY-MM-DD stamp")
    if not stamped:
        failures.append("no stamped fact rows found under references/")

    skill_root = os.path.dirname(HERE)
    for folder, _, names in os.walk(skill_root):
        if os.sep + "fixtures" in folder:
            continue
        for name in names:
            if name.endswith((".md", ".py")):
                with open(os.path.join(folder, name), encoding="utf-8") as source:
                    if EM_DASH in source.read():
                        failures.append(f"{os.path.relpath(os.path.join(folder, name), skill_root)}: contains an em dash")

    if failures:
        print("\n".join(failures))
        print(f"FAILED: {len(failures)} problem(s)")
        return 1
    print(
        f"ok: good fixture is clean, {len(EXPECTED)} bad cases raise {len(covered)} codes, "
        f"the rules-block fix is idempotent, composed and user-scope cases hold, {stamped} facts are stamped"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
