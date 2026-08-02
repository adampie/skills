---
name: sync
description: "Rebase a stack onto a moved trunk, absorb merged layers, and make changes to a lower layer mid-stack, using gh stack sync and gh stack rebase. Use when the user says sync my stack, rebase the stack, main moved, my PR merged, update the stack, or when a change belongs in a branch below the one they are on. Handles rebase conflicts. Does not create pull requests, which stack:submit does."
compatibility: Requires gh 2.0+ with the github/gh-stack extension v0.1.0
metadata:
  author: adampie
  version: "0.1.0"
  tested-against: gh-stack v0.1.0
---

# Sync

Keep a stack correct as the world moves underneath it. Two jobs: catch the stack up with
trunk and merged layers, and put a change into a layer below the current one.

## Refuse first

| Condition | Check |
| --- | --- |
| Not a git repo | `git rev-parse --is-inside-work-tree` fails |
| No stack | `gh stack view --json` fails or lists no branches |
| Rebase already running | `.git/gh-stack-rebase-state` exists |

A rebase already in progress is not a failure to report and stop on. Resume it: resolve
the conflicts per step 3, then `gh stack rebase --continue`, or `--abort` to unwind.

## Which job

Read `gh stack view --json` first, then pick.

| The user wants | Do |
| --- | --- |
| Catch up after trunk moved or a PR merged | Step 1 |
| Change a layer below the current branch | Step 2 |
| Realign layers with no network | `gh stack rebase --no-trunk` |

## Steps

### 1. Catch up

```bash
gh stack sync            # add --prune to delete local branches for merged PRs
```

One command: fetch, mirror the GitHub stack locally, fast-forward trunk, cascade-rebase
every layer, push, and refresh PR state. Squash-merged layers are detected and skipped
via `rebase --onto`, so a merged bottom layer does not replay its commits.

In a non-interactive run, pruning only happens when you pass `--prune`. Ask before
passing it if the user did not say so; it deletes local branches.

**If it reports `Sync aborted`,** the local and remote stacks have diverged and it cannot
prompt. Nothing was changed. Resolve by unstacking and recreating:
`gh stack unstack --local`, then `gh stack checkout <stack-number>` to take the remote
version, or `gh stack init` to rebuild the local one.

### 2. Change a lower layer

Do not patch around a missing lower-layer change from the branch you happen to be on. It
lands the diff in the wrong PR and leaves the lower PR incomplete.

```bash
gh stack down            # or: gh stack checkout <branch>, gh stack bottom
git add <paths>
git commit -m "..."
gh stack rebase --upstack
gh stack top             # or: gh stack checkout <branch you came from>
```

`rebase --upstack` fetches from the remote, so it fails with `no remotes configured` in a
repo that has none. Use `--no-trunk` there.

Commit messages follow the same rules as `stack:commit`.

Push the rewritten branches with `gh stack push`, or `stack:submit` if any layer still
needs a PR. A finished rebase suggests `gh stack submit` regardless; `push` is the right
answer when every layer already has one, since it re-pushes without touching PR bodies.

### 3. Resolve conflicts

`gh stack rebase` and `gh stack sync` exit **3** on a conflict. `sync` restores every
branch to its pre-rebase state first, so the stack is never left half-rebased. Trunk is
the exception: it is fast-forwarded before the rebase starts and stays moved, so the run
is not a no-op even when every branch is restored.

The two commands report differently. `sync` names no files; it only tells you to run
`gh stack rebase`. Do that, and `rebase` prints the conflicted files and the recipe, which
you should follow rather than restate. In short: read the files, resolve the `<<<<<<<`
markers, `git add` each, then `gh stack rebase --continue`. Repeat if another layer
conflicts. Expect a detached HEAD until the rebase finishes.

If the resolution is not obvious, `gh stack rebase --abort` restores everything. Say what
conflicted and stop rather than guessing at someone's intent.

`git rerere` is enabled by `gh stack init`, so a conflict resolved once is replayed
automatically next time. If a first run prompts about it, set `git config rerere.enabled
true` and rerun.

### 4. Report

State the stack bottom to top after the change, one line each, marking what moved:
rebased, merged, pruned, unchanged. Name anything still unpushed.

## Example

User: "I'm on the top branch but this validation belongs in the layer below."

```
$ gh stack down
✓ Checked out store-get, 1 branch down
```

Write the validation there, commit it, then replay everything above:

```
$ gh stack rebase --upstack
✓ Rebased store-get onto config
✓ Rebased user-handler onto store-get
All upstack branches from store-get rebased locally with main (58199fa)
To push up your changes, run `gh stack push`

$ gh stack top && gh stack push
✓ Switched to user-handler
✓ Pushed 3 branches
```

The property worth verifying afterwards is that the change landed in the right PR and
did not leak upward:

```
$ gh pr view 2 --json files    # store-get
  internal/errors.go
  internal/store.go
$ gh pr view 3 --json files    # user-handler, untouched
  internal/api.go
```

## Failure modes

**Exit 3, conflict.** Step 3. Never resolve by taking one side wholesale without reading
both.

**Exit 7, rebase already in progress.** `gh stack rebase --continue` after resolving, or
`--abort` to start over. Do not run `sync`.

**Exit 8, stack is locked.** Another `gh stack` process is writing. Wait and retry; the
lock times out after 5 seconds.

**Exit 6, branch is in multiple stacks.** Check out a branch that belongs to one stack
only, then retry.

**`no remotes configured` on `rebase --upstack`.** The command fetches even when only
rebasing upward. Add `--no-trunk` for a local-only realignment.

**Never** force-push, merge the stack, or run `gh stack modify`, which is interactive and
will hang.
