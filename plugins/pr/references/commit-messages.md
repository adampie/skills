# Commit messages

The same rules whether the change lands as one commit on one branch or as a
layer of a stack. Read the repo's recent history before writing anything:

```bash
git log -20 --format='%s%n%n%b%n---'
```

## Format follows the repo

Match the majority of those 20 commits: Conventional Commits, a ticket prefix,
or plain sentence case. Never introduce a format the repo does not already use,
and never mix two in one stack.

Take a ticket ID from the branch name or from the surrounding commits when the
repo uses one. Inventing one is worse than omitting it.

## Subject

Imperative, sentence case, under 70 characters, British English, no em-dashes,
no hype. Describe the change, not the mechanism.

**Be distinguishable.** If the subject could describe ten other commits in this
repo, sharpen it. "Fix parser bug" is useless to someone scanning the log.

## Body

Only when the diff does not explain itself, and then lead with why. Skip it for
typos, imports, and dependency bumps. Plain text: no markdown headings, no
tables, wrapped at 72 characters.

Cut anything the diff already states. A body that lists the files touched is
noise next to `git show`.

## Attribution

Never add a trailer or footer crediting a tool, and never add a co-author who
did not write code. GitHub attributes a commit by its author email, which the
committing skill checks separately.

## One commit or several

Within a branch, split commits the way the layers of a stack are split: one
concern each, each building on its own. A branch whose commits are "wip", "fix
review", "fix again" is a branch to reshape before it is pushed, not a history
to preserve.
