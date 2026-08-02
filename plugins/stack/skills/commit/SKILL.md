---
name: commit
description: "Split a working tree into an ordered stack of branches, each with its own commits, using the gh-stack GitHub CLI extension. Use when the user wants uncommitted work turned into stacked PRs and says things like commit this as a stack, split this into layers, break this up for review, stack these changes, or start a stack. Also adds a layer on top of an existing stack. Does not push or open pull requests, which stack:submit does."
compatibility: Requires gh 2.0+ and the github/gh-stack extension
metadata:
  author: adampie
  version: "0.1.0"
  tested-against: gh-stack v0.1.0
---

# Commit

Turn a working tree into an ordered chain of branches, each holding one layer of the
change and its own commits. Landing the layers is `stack:submit`.

## Refuse first

Check all of these before touching anything. Report the reason and stop.

| Condition | Check |
| --- | --- |
| Not a git repo | `git rev-parse --is-inside-work-tree` fails |
| Nothing to commit | `git status --porcelain` is empty |
| Detached HEAD | `git symbolic-ref -q HEAD` fails |
| Mid-flight git operation | any of `.git/MERGE_HEAD`, `.git/CHERRY_PICK_HEAD`, `.git/REVERT_HEAD`, `.git/rebase-*`, `.git/gh-stack-rebase-state` exists |
| Extension missing | `gh extension list` has no `gh stack` |

The rebase markers matter because splitting hunks part-way through a rebase writes
commits onto a detached intermediate state that the rebase then discards.

## Never commit secrets

A secret in git history is leaked even after a revert or force-push, because the blob
stays reachable via reflog, forks, CI caches, and anyone who fetched. Scan every hunk
and untracked file you are about to stage.

- **Paths:** `.env*`, `secrets.*`, `credentials.*`, `service-account*.json`, `*.pem`,
  `*.key`, `*.p12`, `id_rsa`, `id_ed25519`, `.netrc`, `.pgpass`, anything under `.ssh/`,
  `.aws/`, `.gnupg/`.
- **Shapes:** `-----BEGIN * PRIVATE KEY-----`, `AKIA*`/`ASIA*`, `gh[pousr]_*`, `xox[abprs]-*`,
  `sk_live_*`, `AIza*`, `sk-*`, long `eyJ*` JWTs.
- **Assignments:** high-entropy values on names matching `KEY`, `SECRET`, `TOKEN`,
  `PASSWORD`, `CLIENT_SECRET`, or connection strings with inline passwords.

Exclude the hunk or file from every layer, tell the user what you found and where before
you start committing, and treat near-misses the same way. A false positive costs one
round trip; a false negative costs a credential rotation.

## Steps

### 1. Read the change

- `git status --porcelain=v1` for paths and states.
- `git diff HEAD` for all tracked modifications.
- Read each untracked file directly; they have no prior version.
- `git log -20 --format='%s%n%n%b%n---'` to learn the repo's message format.
- `gh stack view --json 2>/dev/null` to see whether a stack already exists.

Treat staged, unstaged, and untracked as one pool. Run `git reset` to unstage, so
staging is per-layer from here. Say so in one line; file contents are untouched.

### 2. Plan the layers

Drop the secrets first, then group what is left.

- **One layer is one concern that builds on its own.** Every layer must compile and pass
  on its own, because each becomes a PR that could be the last one merged.
- **Dependencies point down.** If code in layer B needs code in layer A, A is the same
  layer or lower. This constraint outranks every preference below.
- **Group hunks that share a why.** A rename plus its four call sites is one layer, not
  five. Two unrelated changes in one file are two layers.
- **Order:** mechanical setup (dep bumps, config, formatting), then shared foundations
  (models, schemas, utilities), then consumers (handlers, UI), then tests and docs.
- **Do not manufacture layers.** One layer is a fine answer for a small change.

Aim for the fewest layers that keep each one reviewable. Say the plan out loud before
creating anything.

### 3. Create the layers

Pick the path from what `gh stack view --json` returned in step 1.

| Situation | Action |
| --- | --- |
| No stack | `gh stack init <first-layer>` |
| On the top branch | `gh stack add <next-layer>` per layer |
| Not on the top branch | `gh stack top` first, or hand to `stack:sync` if the change belongs lower |

Always pass the branch name. Bare `gh stack init` and `gh stack add` open a prompt and
hang. Names are used verbatim, so `gh stack add refactor/foo` creates `refactor/foo`.

**Ask before starting a stack for a single layer.** If no stack exists and the plan came
out as one layer, `gh stack init` still creates a branch and a stack, which is not what
someone asking to commit a typo expects. Say the change looks like one layer and offer a
plain commit on the current branch instead.

For each layer in order: stage its paths with `git add <paths>`, commit, then
`gh stack add <next>`. Regenerate `git diff HEAD` between layers, since line numbers
shift as commits land. Prefer `git add` over `gh stack add -Am`, which stages everything.

### 4. Write the messages

- **Format follows the repo.** Match the majority of the last 20 commits: Conventional
  Commits, ticket prefix, or plain sentence case. Never introduce a format the repo does
  not already use.
- **Subject:** imperative, sentence case, under 70 characters, British English, no
  em-dashes, no hype. Describe the change, not the mechanism.
- **Be distinguishable.** If the subject could describe ten other commits in this repo,
  sharpen it. "Fix parser bug" is useless to someone scanning the log.
- **Body only when the diff does not explain itself,** and then lead with why. Skip it
  for typos and imports. Plain text; no markdown headings or tables.

### 5. Report

State the stack bottom to top, one line each: `<branch>  <hash>  <subject>`. Then say
what is left in the working tree, and that `stack:submit` opens the PRs.

## Example

User: "commit this, it's a new auth middleware plus the API routes that use it."

1. Preflight passes; no stack exists.
2. Plan: `auth` (middleware plus its test), then `api-routes` (handlers importing it).
   Routes depend on middleware, so middleware goes lower.
3. `gh stack init auth`, `git add auth.go auth_test.go`, commit.
4. `gh stack add api-routes`, `git add api.go`, commit.
5. Report both layers and point at `stack:submit`.

## Failure modes

**`can only add branches to the top of the stack` (exit 5).** You are mid-stack. Run
`gh stack top` to add above, or use `stack:sync` to change a lower layer properly.

**Exit 6, branch belongs to multiple stacks.** Check out a branch that is in one stack
only, then retry.

**`gh: unknown command "stack"`.** Install it pinned:
`gh extension install github/gh-stack --pin v0.1.0`.

**A prompt appears and the run hangs.** A command was called without its argument. Every
`init`, `add`, and `checkout` needs an explicit branch name.
