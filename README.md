<!--
Purpose: Entry point for the skills collection: what each skill does, how to install one, and how to run the checks.
Type: readme-project
-->

# Skills

Agent skills for Claude Code, Codex, and other coding agents, installed with one `npx` command.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Live Checkout](#live-checkout)
- [Resources](#resources)

## Introduction

A skill is a folder of instructions that a coding agent loads when a task
calls for it. This repository holds the skills its author uses every day.
Each skill is self-contained, so you can install one without the others.

| Skill | What It Does |
| --- | --- |
| [grill-me](skills/grill-me/SKILL.md) | Interviews you about a plan or design until every open decision is resolved, then writes the plan. |
| [tokenminator](skills/tokenminator/SKILL.md) | Audits a repository for wasted agent tokens and fixes one area per run. |
| [writing-docs](skills/writing-docs/SKILL.md) | Writes READMEs, guides, requirements, and ADRs to one house style, checked by a linter. |

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/), which provides `npx`. Nothing is built or published.
- [Python 3](https://www.python.org/), for the `tokenminator` and `writing-docs` scripts only.

### Install With `npx skills`

The [skills CLI](https://github.com/vercel-labs/skills) clones this
repository and finds every `skills/<name>/SKILL.md`. It needs no account
and no configuration.

1. List the skills on offer.

   ```bash
   npx skills add choonchernlim/skills --list
   ```

2. Install one skill into the current project. The CLI asks which agents get it.

   ```bash
   npx skills add choonchernlim/skills --skill tokenminator
   ```

3. Or install every skill for every agent.

   ```bash
   npx skills add choonchernlim/skills --all
   ```

4. Add `-g` to install for your user account instead of one project. Add
   `-a` and `-y` to name the agent and skip the prompts.

   ```bash
   npx skills add choonchernlim/skills --skill tokenminator -g -a claude-code -y
   ```

The CLI installs copies, so a new commit here does not reach you on its
own. Fetch newer versions with the update command.

```bash
npx skills update
```

### Install by Hand

Clone the repository, then link one skill folder into the directory your
agent reads. Claude Code reads `~/.claude/skills`. Codex, Copilot, and
OpenCode read `~/.agents/skills`.

```bash
git clone https://github.com/choonchernlim/skills.git
ln -s "$PWD/skills/skills/tokenminator" ~/.claude/skills/tokenminator
```

A link stays current with `git pull`. Copy the folder instead when your
agent does not follow links.

### Usage

Describe the task and the agent picks the matching skill from its
description. You can also name the skill, for example `/tokenminator` in
Claude Code.

#### Run the Checks

Two skills ship a self-test for their script. Run both before you commit a change.

```bash
python3 skills/tokenminator/scripts/test_audit_tokens.py
python3 skills/writing-docs/scripts/test_lint_docs.py
```

## Live Checkout

The author's machines skip the CLI and serve this checkout directly.

- The author's [dotfiles](https://github.com/choonchernlim/dotfiles) clone
  this repository beside themselves.
- `~/.agents/skills` links to the `skills/` folder of that clone, so an
  edit to a skill is live at once.
- Each `rebuild` of the dotfiles pulls the latest commit.
- Agents write runtime state such as `skills/.trash/` into the checkout.
  The `.gitignore` file keeps that state out of commits.

## Resources

| Resource | What It Answers |
| --- | --- |
| [skills CLI](https://github.com/vercel-labs/skills) | Every install flag, the agents it supports, and where it puts the copies |
| [LICENSE](LICENSE) | The MIT terms this repository is shared under |
