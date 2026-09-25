---
name: sync
description: "Bring a pull request branch or a whole stack up to date with trunk, absorb merged work, and make changes to a layer below the current one, using git rebase or gh stack sync. Use when the user says sync this, rebase onto main, main moved, my PR merged, update the branch, my branch is behind, resolve these conflicts, or when a change belongs in a branch below the one they are on. Handles rebase conflicts. Does not create pull requests, which pr:submit does."
compatibility: Requires gh 2.0+, and the github/gh-stack extension v0.1.0 for stacks only
metadata:
  author: adampie
  version: "0.2.0"
  tested-against: gh-stack v0.1.0
---

# Sync

Keep work correct as the world moves underneath it. For a branch that is catching up with
trunk; for a stack it is also absorbing merged layers and putting a change into a layer
below the current one.

## Pick the mode

```bash
gh stack view --json 2>/dev/null
```

Stack mode when that exits 0 and lists a stack containing the current branch. Single mode
otherwise. The rest of this skill marks which steps belong to which.

## Refuse first

| Condition | Check |
| --- | --- |
| Not a git repo | `git rev-parse --is-inside-work-tree` fails |
| On the trunk | current branch equals the default branch, or the stack's `trunk` |
| Mid-flight git operation | a marker below exists and `.git/gh-stack-rebase-state` does not |

```bash
for m in gh-stack-rebase-state MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-apply rebase-merge; do
  [ -e ".git/$m" ] && echo "in progress: $m"
done
```

Read `gh-stack-rebase-state` first, because a gh-stack rebase in flight leaves
`.git/rebase-merge` alongside it. Judge on the other markers alone and you refuse the one
state you are meant to pick up. Test them one at a time: in zsh an unmatched
`.git/rebase-*` glob aborts the command before `ls` runs, checking nothing.

A half-finished merge, cherry-pick, revert, or plain `git rebase` is a refusal: say which
and stop. A gh-stack rebase is not. Resume that one: resolve the conflicts per step 4,
then `gh stack rebase --continue`, or `--abort` to unwind.

An uncommitted working tree stops a rebase in either mode. Commit it with `pr:commit`
first, or say what is in the way and stop.

## Which job

| The user wants | Do |
| --- | --- |
| Catch a branch up after trunk moved | Step 1 |
| Catch a stack up after trunk moved or a PR merged | Step 2 |
| Change a layer below the current branch | Step 3, stack mode |
| Realign layers with no network | `gh stack rebase --no-trunk` |

### 1. Catch up a branch

```bash
git fetch <remote>
git rebase <remote>/<trunk>
```

Rebasing rewrites the branch, so an already-pushed branch then needs a force-push. That is
the one place this skill force-pushes, it is `--force-with-lease` and never `--force`, and
it happens only after the user confirms:

```bash
git range-diff <remote>/<branch>...HEAD    # every commit should pair up
git push --force-with-lease
```

Read the range-diff before pushing. `--force-with-lease` only promises the remote has not
moved since the last fetch, and the fetch above is what makes that promise weak: a commit
somebody else pushed and this run fetched is inside the lease, so dropping it in the rebase
passes the check and loses their work. A commit appearing on the left of the range-diff
with no pair on the right is one about to be deleted.

Prefer a merge when the branch is shared, or when review is already underway and rebasing
would mark the inline comments outdated:

```bash
git merge <remote>/<trunk>
git push
```

Say which of the two was used. Neither is correct in general; the difference is who else
is reading the branch.

### 2. Catch up a stack

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

### 3. Change a lower layer

Stack mode only. Do not patch around a missing lower-layer change from the branch you
happen to be on. It lands the diff in the wrong PR and leaves the lower PR incomplete.

```bash
gh stack down            # or: gh stack checkout <branch>, gh stack bottom
git add <paths>
git commit -m "..."
gh stack rebase --upstack
gh stack top             # or: gh stack checkout <branch you came from>
```

`rebase --upstack` fetches from the remote, so it fails with `no remotes configured` in a
repo that has none. Use `--no-trunk` there.

Commit messages follow `../../references/commit-messages.md`, relative to this skill's
directory, the same as `pr:commit` uses.

Push the rewritten branches with `gh stack push`, or `pr:submit` if any layer still needs
a PR. A finished rebase suggests `gh stack submit` regardless; `push` is the right answer
when every layer already has one, since it re-pushes without touching PR bodies.

### 4. Resolve conflicts

`gh stack rebase` and `gh stack sync` exit **3** on a conflict; plain `git rebase` exits 1.
`sync` restores every branch to its pre-rebase state first, so the stack is never left
half-rebased. Trunk is the exception: it is fast-forwarded before the rebase starts and
stays moved, so the run is not a no-op even when every branch is restored.

The gh-stack commands report differently from each other. `sync` names no files; it only
tells you to run `gh stack rebase`. Do that, and `rebase` prints the conflicted files and
the recipe, which you should follow rather than restate. In short, and the same for a plain
rebase: read the files, resolve the `<<<<<<<` markers, `git add` each, then
`git rebase --continue` or `gh stack rebase --continue`. Repeat if another layer
conflicts. Expect a detached HEAD until the rebase finishes.

If the resolution is not obvious, `--abort` restores everything. Say what conflicted and
stop rather than guessing at someone's intent.

`git rerere` is enabled by `gh stack init`, so a conflict resolved once is replayed
automatically next time. Outside a stack it is off unless the user enabled it; suggest
`git config rerere.enabled true` rather than setting it for them.

### 5. Report

State where the work sits after the change, one line each, marking what moved: rebased,
merged, pruned, unchanged. Name anything still unpushed, and say whether the push was a
force-with-lease.

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

On a single branch, the equivalent run is a fetch, a rebase, and a checked force-push:

```
$ git fetch origin && git rebase origin/main
Successfully rebased and updated refs/heads/store-get.

$ git range-diff origin/store-get...HEAD
1:  e1fe8c9 = 1:  7c4a02b Add Store.Get to look up a user by ID
```

Both commits pair with `=`, so nothing is being dropped, and the push is safe to confirm.

## Failure modes

**Exit 3, conflict.** Step 4. Never resolve by taking one side wholesale without reading
both.

**Exit 7, rebase already in progress.** `gh stack rebase --continue` after resolving, or
`--abort` to start over. Do not run `sync`.

**Exit 8, stack is locked.** Another `gh stack` process is writing. Wait and retry; the
lock times out after 5 seconds.

**Exit 6, branch is in multiple stacks.** Check out a branch that belongs to one stack
only, then retry.

**`no remotes configured` on `rebase --upstack`.** The command fetches even when only
rebasing upward. Add `--no-trunk` for a local-only realignment.

**`stale info` from `push --force-with-lease`.** The remote branch moved after the fetch.
Fetch again, read the new commits, and decide with the user. Never reach for `--force`.

**Never** force-push a shared branch without saying so, merge a PR, or run
`gh stack modify`, which is interactive and will hang.
