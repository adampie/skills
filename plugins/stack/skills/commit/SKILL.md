---
name: commit
description: "Split a working tree into an ordered stack of branches, each with its own commits, using the gh-stack GitHub CLI extension. Use when the user wants uncommitted work turned into stacked PRs and says things like commit this as a stack, split this into layers, break this up for review, stack these changes, or start a stack. Also adds a layer on top of an existing stack. Does not push or open pull requests, which stack:submit does."
compatibility: Requires gh 2.0+ with the github/gh-stack extension v0.1.0, and betterleaks for secret scanning
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
| Mid-flight git operation | the marker loop below prints anything |
| Extension missing | `gh extension list` has no `gh stack` |

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

After staging each layer and **before** committing it, scan what is staged:

```bash
betterleaks git --staged --verbose --redact --no-banner
```

Exit 0 is clean, exit 1 means findings. `--redact` keeps the secret itself out of the
transcript, and `--staged` covers new files that `--pre-commit` would miss, since that
one scans `git diff` and untracked files are not in it.

On a finding: `git restore --staged <path>` to unstage it, drop it from every layer, and
tell the user what was found and where before going any further. A false positive costs
one round trip; a false negative costs a credential rotation.

betterleaks judges content, not whether a path belongs in git. A `.env` or `*.pem` whose
contents look unremarkable still passes, so exclude those on sight.

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
nothing but trunk. Nothing warns you. `stack:submit` reads that record, treats the PR as
this stack's own, and pushes the new commits over it. Reusing a name from a stack you
abandoned is the common way in.

**Ask before starting a stack for a single layer.** If no stack exists and the plan came
out as one layer, `gh stack init` still creates a branch and a stack, which is not what
someone asking to commit a typo expects. Say the change looks like one layer and offer a
plain commit on the current branch instead.

For each layer in order: stage its paths with `git add <paths>`, commit, then
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

User: "commit this sensibly." Working tree holds `config.yaml` (new), `internal/store.go`
(a new `Get` method), `internal/api.go` (new, calls `Get`), and `.env`.

Preflight passes and no stack exists. `.env` is dropped on sight as a path that does not
belong in git. The rest plans into three layers: `config.yaml` is mechanical, `store.go`
is foundational, and `api.go` calls `Get` so it must sit above `store.go`.

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
Next: stack:submit opens one PR per layer.
```

## Failure modes

**`can only add branches to the top of the stack` (exit 5).** You are mid-stack. Run
`gh stack top` to add above, or use `stack:sync` to change a lower layer properly.

**Exit 6, branch belongs to multiple stacks.** Check out a branch that is in one stack
only, then retry.

**`gh: unknown command "stack"`.** Install it pinned:
`gh extension install github/gh-stack --pin v0.1.0`.

**Never rename a stacked branch with `git branch -m`.** There is no `gh stack rename`, and
the extension does not notice: the old name stays in the stack as a layer with no commits,
and the renamed branch drops out of the stack entirely. The state lives in `.git/gh-stack`,
a JSON file keyed by branch name, so recovery means editing that file by hand to rename
the entry. Get the name right at creation instead.

**A prompt appears and the run hangs.** A command was called without its argument. Every
`init`, `add`, and `checkout` needs an explicit branch name.
