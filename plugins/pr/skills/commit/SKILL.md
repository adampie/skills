---
name: commit
description: "Commit a working tree onto a branch ready for review: one branch when the change is one pull request, or an ordered stack of branches when it needs layers, using the gh-stack GitHub CLI extension. Use when the user says commit this, commit this sensibly, put this on a branch, get this ready for review, or wants uncommitted work turned into stacked PRs with commit this as a stack, split this into layers, break this up for review. Also adds a layer on top of an existing stack. Does not push or open pull requests, which pr:submit does."
compatibility: Requires gh 2.0+, betterleaks for secret scanning, and the github/gh-stack extension v0.1.0 for stacks only
metadata:
  author: adampie
  version: "0.2.0"
  tested-against: gh-stack v0.1.0
---

# Commit

Turn a working tree into committed branches. One branch when the change reviews
as a single pull request, an ordered chain of branches when it does not. Raising
the pull requests is `pr:submit`.

## Refuse first

Check all of these before touching anything. Report the reason and stop.

| Condition | Check |
| --- | --- |
| Not a git repo | `git rev-parse --is-inside-work-tree` fails |
| Nothing to commit | `git status --porcelain` is empty |
| Detached HEAD | `git symbolic-ref -q HEAD` fails |
| Mid-flight git operation | the marker loop below prints anything |
| Extension missing, stacks only | `gh extension list` has no `gh stack` |

Test the markers one at a time rather than with a glob:

```bash
for m in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-apply rebase-merge gh-stack-rebase-state; do
  [ -e ".git/$m" ] && echo "in progress: $m"
done
```

Silence means clear. A bare `ls .git/MERGE_HEAD .git/rebase-*` is not equivalent: in
zsh an unmatched `.git/rebase-*` aborts the command before `ls` runs, so it prints
`no matches found` and checks none of the paths, including ones that do exist.

The rebase markers matter because splitting hunks part-way through a rebase writes
commits onto a detached intermediate state that the rebase then discards.

**Check the identity before committing, and never set it.** Compare the configured address
against the global config and the authors of recent history:

```bash
git config user.email
git config --global user.email
git log -20 --format='%ae' | sort | uniq -c | sort -rn | head -3
```

Ask before committing only when the configured address matches **neither** the global
config nor an author in that list. A local override disagreeing with both is the case
worth stopping for.

Say nothing when it equals the global address, however unfamiliar this repo's history
looks. A repo with a handful of commits, or one seeded by an earlier run that got the
identity wrong, is no evidence against it, and prompting there teaches the user to wave
the check through.

GitHub attributes a commit by email, so an unrecognised one produces commits that show
"No user is associated with the committer email" and never link to the author's profile.
Fixing that after the fact means rewriting history and force-pushing.

Use whatever git is already configured to use. Never run `git config user.email <address>`,
and do not take an address from conversation context; a fresh `git init` inherits the
global config, which is nearly always the right answer.

## Never commit secrets

A secret in git history is leaked even after a revert or force-push, because the blob
stays reachable via reflog, forks, CI caches, and anyone who fetched.

After staging each commit and **before** making it, scan what is staged:

```bash
betterleaks git --staged --verbose --redact --no-banner
```

Exit 0 is clean, exit 1 means findings. `--redact` keeps the secret itself out of the
transcript, and `--staged` covers new files that `--pre-commit` would miss, since that
one scans `git diff` and untracked files are not in it.

On a finding: `git restore --staged <path>` to unstage it, drop it from every commit, and
tell the user what was found and where before going any further. A false positive costs
one round trip; a false negative costs a credential rotation.

betterleaks judges content, not whether a path belongs in git. A `.env` or `*.pem` whose
contents look unremarkable still passes, so exclude those on sight.

## Steps

### 1. Read the change

- `git status --porcelain=v1` for paths and states.
- `git diff HEAD` for all tracked modifications.
- Read each untracked file directly; they have no prior version.
- `git branch --show-current` and `git log --oneline -5` for where HEAD sits.
- `gh stack view --json 2>/dev/null` to see whether a stack already exists.

Treat staged, unstaged, and untracked as one pool. Run `git reset` to unstage, so
staging is per-commit from here. Say so in one line; file contents are untouched.

### 2. Decide the shape

Drop the secrets first, then group what is left into concerns: one concern is one
thing that builds, passes and reviews on its own.

| Situation | Shape |
| --- | --- |
| One concern | One branch, step 3 |
| Several concerns, independent of each other | One branch each, committed and submitted separately |
| Several concerns that stack: B needs A | A stack, step 4 |
| A stack already exists and HEAD is in it | A stack, step 4 |
| The user asked for a stack | A stack, step 4 |

**One branch is the default.** A stack costs the reviewer a chain to follow and the
author a rebase every time a layer merges, so it earns its place only when the parts
genuinely depend on each other and are worth reviewing apart. Say which shape the change
came out as and why, before creating anything.

When grouping:

- **Dependencies point down.** If code in layer B needs code in layer A, A is the same
  layer or lower. This constraint outranks every preference below.
- **Group hunks that share a why.** A rename plus its four call sites is one layer, not
  five. Two unrelated changes in one file are two layers.
- **Order:** mechanical setup (dep bumps, config, formatting), then shared foundations
  (models, schemas, utilities), then consumers (handlers, UI), then tests and docs.
- **Do not manufacture layers.** Aim for the fewest that keep each one reviewable.

### 3. One branch

Commit on the current branch when HEAD is already on a feature branch. When HEAD is on
trunk, create one first:

```bash
git checkout -b <name>
```

Name it the way the repo already names branches, from `git branch -r --sort=-committerdate`,
and check the name is free by the rules in step 4. A ticket ID in the change gets the
branch name the tracker suggests.

Then, per concern: `git add <paths>`, scan, `git commit`. Several small commits on one
branch are fine and often better than one; `pr:submit` writes the PR body from all of
them.

### 4. A stack

Pick the path from what `gh stack view --json` returned in step 1.

| Situation | Action |
| --- | --- |
| No stack | `gh stack init <first-layer>` |
| On the top branch | `gh stack add <next-layer>` per layer |
| Not on the top branch | `gh stack top` first, or hand to `pr:sync` if the change belongs lower |

Always pass the branch name. Bare `gh stack init` and `gh stack add` open a prompt and
hang. Names are used verbatim, so `gh stack add refactor/foo` creates `refactor/foo`.

**Check every name is free first, locally and on the remote.** Pick another name and tell
the user if either check hits:

```bash
git remote                                        # which remote to check
git rev-parse --verify --quiet <name>             # local branch
git ls-remote --exit-code --heads <remote> <name> # remote branch
```

Take the sole remote if there is one, `origin` when there are several, and skip the remote
check when `git remote` prints nothing. A hardcoded `origin` in a repo without one exits
128 with `does not appear to be a git repository`, which reads as neither free nor taken.

`gh stack add` happily creates a layer whose name matches an abandoned remote branch from
an earlier stack, and `gh stack view` then binds that layer to the old branch's open PR by
name alone, writing the PR number into `.git/gh-stack` even though the two histories share
nothing but trunk. Nothing warns you. `pr:submit` reads that record, treats the PR as this
stack's own, and pushes the new commits over it. Reusing a name from a stack you abandoned
is the common way in.

For each layer in order: stage its paths with `git add <paths>`, scan, commit, then
`gh stack add <next>`. Regenerate `git diff HEAD` between layers, since line numbers
shift as commits land. Prefer `git add` over `gh stack add -Am`, which stages everything.

**Splitting one file across layers.** When a file carries changes belonging to different
layers, do not reach for `git add -p`: it is interactive and will hang. Adjacent edits
also arrive as a single hunk, so there is often nothing to split by hunk anyway. Write the
intermediate version of the file instead, and restore the full one afterwards:

```bash
mktemp -d                                 # use the printed path as <dir>
cp internal/store.go <dir>/store.full.go  # keep the finished version
# write internal/store.go holding only the lower layer's changes
git add internal/store.go && git commit -m "..."
gh stack add <next-layer>
cp <dir>/store.full.go internal/store.go  # the rest becomes the next layer
git add internal/store.go && git commit -m "..."
```

A fixed path like `/tmp/store.full.go` is another run's path too, and the finished version
of the file is the only copy that exists at that point.

Check with `git diff <lower>..<upper> -- <path>` that the upper layer adds only what you
meant to defer.

### 5. Write the messages

`../../references/commit-messages.md`, relative to this skill's directory, holds the
rules, and they are the same in both shapes. Read it before writing the first message,
not after.

### 6. Report

State what was committed, oldest first, one line each: `<branch>  <hash>  <subject>`.
Then say what is left in the working tree, and that `pr:submit` opens the pull requests.

## Example

User: "commit this sensibly." Working tree holds `config.yaml` (new), `internal/store.go`
(a new `Get` method), `internal/api.go` (new, calls `Get`), and `.env`.

Preflight passes and no stack exists. `.env` is dropped on sight as a path that does not
belong in git. The rest is three concerns and `api.go` calls `Get`, so they stack rather
than sit side by side: `config.yaml` is mechanical, `store.go` is foundational, and
`api.go` must sit above `store.go`.

Each layer is staged, scanned, then committed:

```bash
gh stack init config      && git add config.yaml       && betterleaks git --staged --redact --no-banner && git commit -m "..."
gh stack add store-get    && git add internal/store.go && betterleaks git --staged --redact --no-banner && git commit -m "..."
gh stack add user-handler && git add internal/api.go   && betterleaks git --staged --redact --no-banner && git commit -m "..."
```

Had `.env` been staged, the scan would have stopped the commit:

```
┌─github-pat──○
│ 2 │ GITHUB_TOKEN=REDACTED
│   │              ^^^^^^^^
│   path ............. .env
└○
leaks found: 1
```

Result reported to the user:

```
Stack on main, bottom to top:

  config        792c081  Add request timeout and retry configuration
  store-get     e1fe8c9  Add Store.Get to look up a user by ID
  user-handler  14735c1  Add the user endpoint handler

Left in the working tree: .env (excluded, contains credentials)
Next: pr:submit opens one PR per layer.
```

Without `api.go`, the same change is one concern on one branch:

```bash
git checkout -b store-get && git add config.yaml internal/store.go \
  && betterleaks git --staged --redact --no-banner && git commit -m "..."
```

## Failure modes

**`can only add branches to the top of the stack` (exit 5).** You are mid-stack. Run
`gh stack top` to add above, or use `pr:sync` to change a lower layer properly.

**Exit 6, branch belongs to multiple stacks.** Check out a branch that is in one stack
only, then retry.

**`gh: unknown command "stack"`.** Install it pinned:
`gh extension install github/gh-stack --pin v0.1.0`. Only stacks need it; a single branch
is plain git.

**Never rename a stacked branch with `git branch -m`.** There is no `gh stack rename`, and
the extension does not notice: the old name stays in the stack as a layer with no commits,
and the renamed branch drops out of the stack entirely. The state lives in `.git/gh-stack`,
a JSON file keyed by branch name, so recovery means editing that file by hand to rename
the entry. Get the name right at creation instead.

**A prompt appears and the run hangs.** A command was called without its argument. Every
`init`, `add`, and `checkout` needs an explicit branch name.
