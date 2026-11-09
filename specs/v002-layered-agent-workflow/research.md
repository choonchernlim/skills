# v002: Research

What published research and proven practice say about running coding agents across a stable
branch, a feature branch and worktree branches. Each section answers one question and names the
design decisions it informs. The [scorecard](#decision-scorecard) rates every decision.

Evidence labels:

- **Peer:** peer-reviewed.
- **Survey:** large-scale industry research.
- **Docs:** vendor documentation.
- **Preprint:** not yet peer-reviewed.
- **Practice:** a practitioner or vendor report.
- **Secondary:** read through a review of the paper, not the paper itself.

## Table of Contents

- [Q1 Branch Layers and Sync Cadence](#q1-branch-layers-and-sync-cadence)
- [Q2 Parallel Agents in Worktrees](#q2-parallel-agents-in-worktrees)
- [Q3 Conflict Resolution by Models](#q3-conflict-resolution-by-models)
- [Q4 Work Sizing](#q4-work-sizing)
- [Q5 Approval and Integration Review](#q5-approval-and-integration-review)
- [Q6 Practitioner Worktree Workflows](#q6-practitioner-worktree-workflows)
- [Decision Scorecard](#decision-scorecard)
- [What This Changed in the Design](#what-this-changed-in-the-design)
- [Gaps](#gaps)

## Q1 Branch Layers and Sync Cadence

Informs D1, D2 and D4.

### Branch Lifetime

- **Short branches win.** Trunk-based branches "last no more than a few hours". Teams keep three or fewer active branches and merge at least once a day.
  - [DORA, Trunk-based development](https://dora.dev/capabilities/trunk-based-development/). Survey.
- **Big merges hurt through uncertainty.** "The problem with big merges is not so much the work involved with them, it's the uncertainty of that work."
  - [Fowler, Patterns for Managing Source Code Branches, 2020](https://martinfowler.com/articles/branching-patterns.html). Practice.
- **Clean merges can still break.** A semantic conflict merges cleanly, then fails at build or run time. Self-testing code is the guard.
  - Fowler, same source. Practice.
  - Conflicts were frequent and persistent across 9 systems, often surfacing as later build or test failures: [Brun et al., TSE 2013](https://homes.cs.washington.edu/~mernst/pubs/vc-conflicts-tse2013-abstract.html). Peer.
- **Most conflicts are small.** 94% of conflicting chunks are 50 lines or fewer, and about 81% keep existing content. 10 to 20% of merges conflict.
  - Ghiotto et al., On the Nature of Merge Conflicts, TSE 2020, via [its review](https://neverworkintheory.org/2021/08/12/on-the-nature-of-merge-conflicts.html). Peer, secondary.
- **No source gives a polling interval.** The evidence supports integrating at least daily and at events. Nothing found supports a fixed 15-minute check.

### Merge Tools

- **Never rebase shared history.** "Do not rebase commits that exist outside your repository and that people may have based work on." Rebasing local commits is fine.
  - [Pro Git, Rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing). Docs.
- **rerere replays resolutions.** It reuses a recorded resolution when a conflict recurs, as on repeated rebases. It must be enabled, and it does not stage files.
  - [git-rerere](https://git-scm.com/docs/git-rerere). Docs.
- **Merge queues serve many submitters.** A queue tests each change on the latest base plus the changes ahead of it. A solo developer gains little.
  - [GitHub, Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue). Docs.

## Q2 Parallel Agents in Worktrees

Informs D4, D5, D6 and D11.

### Isolation

- **Worktrees are the documented isolation.** `claude -w <name>` creates `.claude/worktrees/<name>/` on a new branch, `worktree-<name>`, one per parallel session.
  - [Claude Code, Run parallel sessions with worktrees](https://code.claude.com/docs/en/worktrees). Docs.
- **The default base is not your feature branch.** New worktrees branch from the remote default branch unless `worktree.baseRef` is `"head"`. A named branch needs `git worktree add`.
  - Same source.
- **A session can move mid-run.** `EnterWorktree` with a path switches the session. A path outside `.claude/worktrees/` asks for approval first.
  - Same source. Hooks keep `${CLAUDE_PROJECT_DIR}` at the original root and get the worktree from `cwd`.
- **A worktree session stays out of the main checkout.** Claude Code blocks its edits there and git commands redirected there. Git also refuses to update a branch checked out elsewhere.
  - Same source, and [git-worktree](https://git-scm.com/docs/git-worktree). Docs.
- **Sessions can talk.** Cross-session messaging lets sessions in different worktrees pass findings to each other.
  - Same source.
- **Few parallel sessions.** "Three focused teammates often outperform five scattered ones." Two teammates editing one file overwrite each other.
  - [Claude Code, Agent teams](https://code.claude.com/docs/en/agent-teams). Docs.
  - No controlled study of how many sessions one developer can supervise was found.
- **Parallel agents suit reading, not shared writing.** A multi-agent research system beat one agent by 90.2%, at about 15 times the tokens. Coding has fewer parallel tasks.
  - [Anthropic, How we built our multi-agent research system, 2025](https://www.anthropic.com/engineering/multi-agent-research-system). Practice.
  - Parallel writers make conflicting decisions: [Cognition, Don't Build Multi-Agents, 2025](https://cognition.com/blog/dont-build-multi-agents). Practice.

### Loops and Consistency

- **`/loop` lives and dies with its session.** It fires only while the session is open and idle, and a recurring task expires after 7 days.
  - A run can start late by up to half its interval.
  - A fixed-interval loop stops only when you ask Claude to cancel it.
  - Unattended schedules belong in Desktop or cloud scheduled tasks; Monitor and Channels replace polling.
  - [Claude Code, Run prompts on a schedule](https://code.claude.com/docs/en/scheduled-tasks). Docs.
- **Must-always rules belong in hooks and checks.** Keep CLAUDE.md short, and enforce with hooks. A Stop hook must guard against looping.
  - [Claude Code, Best practices](https://code.claude.com/docs/en/best-practices) and [hooks guide](https://code.claude.com/docs/en/hooks-guide). Docs.
- **Build from a written spec.** Write the spec, build from it in a fresh session, then have a reviewer check the diff against that spec.
  - Same best practices source.

## Q3 Conflict Resolution by Models

Informs D3 and D12.

- **Models are right about half the time.** The best published results sit between 55 and 68%.
  - MergeBERT reached 63 to 68%, about three times the structured tools: [Svyatkovskiy et al., ESEC/FSE 2022](https://arxiv.org/abs/2109.00084). Peer.
  - Models matched the developer on about 55% of real Java conflicts, against 36.7% for the best traditional tool: [Shen, 2026](https://arxiv.org/abs/2607.27674). Preprint.
  - The best models resolve under 60% of 7,938 hunks: [Merge-Bench, 2026](https://arxiv.org/abs/2605.25890). Preprint.
- **A model must not judge structure.** An LLM judge accepted 4 of 5 resolutions that failed a deterministic structural check.
  - [Shen, 2026](https://arxiv.org/abs/2607.27674). Preprint.
- **Telling an agent what changed helps.** In constructed tasks, a message describing the concurrent change recovered 82% of runs. The authors warn these rates do not estimate practice.
  - Interference hit 97% of constructed runs, but only 1 of 834 runs on real Django pull requests: [Passes Alone, Fails Together, 2026](https://arxiv.org/abs/2609.25396). Preprint.
- **Agent pull requests conflict often.** 27.67% of 107,000 simulated agent pull requests conflicted.
  - [AgenticFlict, 2026](https://arxiv.org/abs/2604.03551). Preprint.

## Q4 Work Sizing

Informs D7 and D8.

- **Proven changes are small.** At Google the median change is 24 lines, and about 90% touch fewer than 10 files.
  - [Sadowski et al., Modern Code Review: A Case Study at Google, ICSE-SEIP 2018](https://sback.it/publications/icse2018seip.pdf). Peer. It describes the process, not a causal safety effect.
- **Review quality drops past 400 lines.** Review 200 to 400 lines at a time, for under 60 minutes.
  - [SmartBear, Best Practices for Peer Code Review](https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/), from a Cisco study of 2,500 reviews. Practice.
- **Small batches speed feedback.** A batch that takes over a week to finish and check is too big.
  - [DORA, Working in small batches](https://dora.dev/capabilities/working-in-small-batches/). Survey.
- **One concern per change.** Up to 15% of bug fixes were tangled with other work, which corrupts later analysis.
  - [Herzig and Zeller, The impact of tangled code changes, MSR 2013](https://www.microsoft.com/en-us/research/publication/the-impact-of-tangled-code-changes/). Peer.
- **Agents overreach without a limit.** "The agent tended to try to do too much at once." One feature per session, ending in a commit and a clean state, fixed it.
  - [Anthropic, Effective harnesses for long-running agents, 2025](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). Practice.
- **No source sets a step or file threshold.** Spec tools isolate per feature, with no size rule.
  - [Kiro, Spec best practices](https://kiro.dev/docs/specs/best-practices/) splits work into specs to avoid conflicts. Docs.
  - [GitHub Spec Kit](https://github.com/github/spec-kit) makes one branch per feature spec. Docs.

## Q5 Approval and Integration Review

Informs D9 and D10.

- **Uniform prompts become rubber stamps.** Users accept 93% of permission prompts, and "people stop paying close attention to what they're approving".
  - [Anthropic, How we built Claude Code auto mode, 2026](https://www.anthropic.com/engineering/claude-code-auto-mode). Practice.
- **Automation bias is measurable.** Wrong automated advice raised the risk of a wrong decision by 26%. Workload raises it; accountability lowers it.
  - [Goddard et al., Automation bias: a systematic review, JAMIA 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751/). Peer. The studies are clinical, not coding.
- **Review is mostly about understanding.** Defects motivate review, but reviewers mainly struggle to understand the change and its context.
  - [Bacchelli and Bird, Modern Code Review, ICSE 2013](https://web.eecs.umich.edu/~weimerw/2018-481/readings/codereview.pdf). Peer.
- **One reviewer is the norm.** Under 25% of Google changes have more than one reviewer.
  - [Sadowski et al., 2018](https://sback.it/publications/icse2018seip.pdf). Peer.
- **No source covers batch review triggers.** Nothing found compares every N merges, each pull request, and a schedule.
  - The design rests on the review-size and context findings above.

## Q6 Practitioner Worktree Workflows

Informs D13 and D14. Every source here is practice, and none measures an outcome.

- **An integration branch sits between worktrees and the stable branch.** Merge the worktree branches there, test, fix conflicts, then promote the result.
  - [MindStudio, Git Worktrees for AI Coding](https://www.mindstudio.ai/blog/git-worktrees-parallel-ai-coding-agents). Practice.
- **Rebase each branch right before it merges.** One source calls "Rebase Before PR" the most widely recommended convention, with no evidence behind it.
  - [Zylos, Git Worktree Isolation Patterns, 2026](https://zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development/). Practice.
  - A practitioner rebases "each branch onto main right before it merges instead of doing one big merge at the end": [DEV, Claude Code Worktrees](https://dev.to/jcamarate/claude-code-worktrees-parallel-agents-without-the-conflicts-3fnl), a reader comment. Practice.
- **Merge one branch at a time, in dependency order.** Zylos merges each with `--no-ff` and fixes conflicts before the next.
  - Same Zylos and MindStudio sources. Practice.
- **Split work by boundary before agents start.** "Avoid splitting work that touches the same files from different directions."
  - MindStudio, same source. Practice.
- **Remove each worktree once it merges.** "Worktrees don't clean themselves up."
  - MindStudio, same source. Practice.
- **Tools merge each workspace through its own pull request path.** Conductor gives each workspace a branch, checks and a pull request, then archives it.
  - [Conductor, Run multiple Claude Code sessions](https://www.conductor.build/docs/guides/parallel-agents/run-multiple-claude-code-sessions). Docs.
- **No source syncs on a timer.** Every workflow found syncs with the base at an event: worktree start, before merge, or before the pull request.

## Decision Scorecard

| # | Decision | Verdict | Why | Change It Suggests |
| --- | --- | --- | --- | --- |
| D1 | Merge `develop` into the shared feature branch; never rebase it | ✅ Supported | Never rewrite shared history | None |
| D2 | Rebase a worktree branch onto the feature branch at start and before merging up | ✅ Supported | Local history may be rebased | Turn on `rerere` |
| D3 | An agent resolves conflicts by the plan, tests gate, you approve | ✅ Supported | Models are right about half the time | Deterministic checks and tests gate it; never a model judge |
| D4 | A 15-minute `/loop` watches for parent changes | 🟡 Weakened | No interval has support; `/loop` dies with its session | Sync at events, plus a daily `develop` merge; `/loop` optional |
| D5 | One worktree per problem, one session each, from the feature HEAD | ✅ Supported | Documented isolation | Create from HEAD; keep three or fewer active |
| D6 | Detect a linked worktree with git; move with `EnterWorktree` | ✅ Supported | Plain git plus a documented tool | None |
| D7 | Recommend a worktree above 3 steps or 3 files | 🟡 Weakened | No threshold has a source | Count concerns, commits and expected lines instead |
| D8 | Offer to move the plan's work into a worktree midway | ✅ Supported | One concern per change | None |
| D9 | You approve every commit, merge and push | 🟡 Weakened | 93% acceptance; automation bias | Keep it, with gates that show size and risk; your call |
| D10 | Integration review before each PR, nudged after 3 merges | 🟡 Weakened | No source tests the trigger | Nudge on combined size; one reviewer by default |
| D11 | Rules live in skills plus scripts, not long instruction files | ✅ Supported | Enforcement belongs in hooks and checks | Must-always rules go in hooks or checks |
| D12 | Tell sibling worktrees what changed after each merge-up | 🟡 Weakened | It helped in constructed tasks; real interference was rare | Drop it: each worktree rebases before it merges |
| D13 | Merge `develop` into the feature branch at events, not on a timer | ✅ Supported | Every workflow found syncs at events | Merge at each worktree merge and before the pull request |
| D14 | Merge a worktree from its own session, pushing to the remote feature branch | 🟡 Weakened | No source tests it; it follows the pull request path tools use | Rejected pushes retry, so racing merges stay safe |

> **Legend:** *✅ the evidence backs it · 🟡 the evidence weakens it or is silent*

## What This Changed in the Design

| Earlier Draft | Now | Evidence |
| --- | --- | --- |
| A `/loop` and a session hook watch `develop`, then merge and push it alone | `develop` merges at each worktree merge and feature review | [D13](#decision-scorecard): every workflow found syncs at events |
| Agent-resolved `develop` conflicts pushed if the checks pass | The same conflicts show in the gate ② packet first | [D3](#decision-scorecard): models resolve about half of conflicts right |
| `up` in the worktree, then `merge vN` in the feature checkout | One `/merge-worktree`, pushing to the remote feature branch | [D14](#decision-scorecard); git cannot move a branch checked out elsewhere |
| Sibling worktrees get a summary of each merge | Dropped: each worktree rebases before it merges | [D12](#decision-scorecard) |
| A worktree is Recommended above 3 steps or 3 files | Split multi-concern plans first; Recommended at about 400 lines | [D7](#decision-scorecard): no threshold has a source |
| Every gate is a plain approval | Three gates, each with the work checked; gate ② shows a full packet | [D9](#decision-scorecard): users approve 93% of prompts |
| Integration review after 3 merges, three reviewers | `/review-feature` when you choose; simplify and architecture always | [D10](#decision-scorecard), and your request |

## Gaps

- No study ties branch age to conflict rate directly.
- No controlled study measures how many agent sessions one developer can supervise.
- No source tests when to run an integration review or which reviewers it needs.
- The conflict-resolution benchmarks are 2026 preprints, not yet peer-reviewed.
