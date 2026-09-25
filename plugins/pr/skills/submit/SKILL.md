---
name: submit
description: "Push committed work to GitHub and create or update its pull requests: one PR for a branch, or one per layer for a stack created with the gh-stack CLI extension. Use when the user says open a PR, raise this for review, put this up, push this up, submit the stack, open the PRs, or mark them ready. Opens drafts by default, writes the title and body, and assigns the author. Does not commit, which pr:commit does, and never merges."
compatibility: Requires gh 2.0+, and the github/gh-stack extension v0.1.0 for stacks only
metadata:
  author: adampie
  version: "0.2.0"
  tested-against: gh-stack v0.1.0
---

# Submit

Push what is committed and open or update the pull requests it needs: one for a plain
branch, or one per layer for a stack, each based on the layer below. Making the commits
is `pr:commit`.

## Pick the mode

```bash
gh stack view --json 2>/dev/null
```

Stack mode when that exits 0 and lists a stack containing the current branch. Single mode
otherwise, including when the extension is not installed. Say which mode the run is in
before doing anything that touches GitHub; the two differ in what they push and in what
they leave in the PR body.

## Refuse first

| Condition | Check |
| --- | --- |
| Not a git repo | `git rev-parse --is-inside-work-tree` fails |
| No remote | `git remote` is empty |
| Not authenticated | `gh auth status` fails |
| On the trunk | current branch equals the default branch, or the stack's `trunk` |
| Nothing to submit | `git log <trunk>..HEAD` is empty |

Read the trunk from the stack in stack mode, and otherwise from the repo:

```bash
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
```

A dirty working tree is a warning, not a refusal: say the uncommitted changes will not be
in the PRs and suggest `pr:commit`, then continue with what is committed.

## Steps

### 1. Read what will be submitted

**Single mode.** `git log <trunk>..HEAD` and `git diff <trunk>...HEAD` for the change, and
`gh pr view --json number,state,isDraft,baseRefName 2>/dev/null` for whether this branch
already has a PR. An open PR means this run updates it rather than creating one; a merged
or closed one means `gh pr create` opens a second PR on the same branch, so say so and
confirm before continuing.

**Stack mode.** `gh stack view --json`. Record `trunk`, and each branch with its `pr` and
`isMerged`. Branches without a `pr` are the ones that will be created. v0.1.0 does not
emit a `head` field per branch, whatever older docs show. Do not parse one.

**Confirm each recorded PR is actually this stack's.** For every branch that has a `pr`,
check its base is the layer below, or `trunk` for the bottom layer:

```bash
gh pr view <number> --json number,headRefName,baseRefName
```

Stop and tell the user if a base points somewhere else. A `pr` record can be a stale match
rather than a PR this stack opened: `gh stack view` binds a layer to any open PR whose head
branch has the same name, so a layer reusing a name from an abandoned stack inherits that
stack's PR. Submitting then pushes unrelated commits onto it and retargets its base, which
step 4 does silently because updating existing PRs is its normal job. Recovering means
renaming the layer, which `pr:commit` covers, and hand-editing `.git/gh-stack`.

### 2. Draft the titles and bodies

`../../references/pr-description.md`, relative to this skill's directory, holds the rules.
Read it before writing, and write the text now in both modes: in stack mode
`gh stack submit` has no title or body flag and auto-generates from the commits, so the
real text is applied afterwards with `gh pr edit` in step 5.

One title and body per pull request, each written against that PR's own diff.

### 3. Preview and confirm

Opening PRs notifies reviewers and starts CI, so show the plan and wait for a go-ahead:

```
Stack: auth -> api-routes -> ui   (base: main)
Mode:  DRAFT                      (say "ready" to open for review)

  1. auth        Add token verification middleware
  2. api-routes  Add the user routes behind the new middleware
  3. ui          Add the dashboard that reads the user routes
```

A single PR is the same preview with one line. Default to draft in both modes. Open ready
only when the user asks.

### 4. Push and open

**Single mode.** Push the branch, then create or update:

```bash
git push -u <remote> HEAD
gh pr create --draft --base <trunk> --title "..." --body-file <dir>/body.md --assignee @me
```

Push explicitly rather than letting `gh pr create` do it: on a fork it asks where to push
and hangs. Drop `--draft` only when the user asked for ready. When the branch already has
an open PR, the push alone updates it, and title and body change only if the user asked to
refresh them:

```bash
gh pr edit <number> --title "..." --body-file <dir>/body.md
```

Single mode has no attribution block to remove, so step 5 does not apply to it. Never add
one either: no generated-with footer, no tool credit.

**Stack mode.**

```bash
gh stack submit --auto          # add --open only when the user asked for ready
```

`--auto` is required. Without it the command prompts for a title per PR and hangs. Add
`--remote <name>` if the repo has several remotes.

Stacked PRs are in public preview, so treat availability as given. Expect exit 0 and one
PR per unmerged layer, with each base pointing at the layer below.

### 5. Apply the real titles and bodies (stack mode)

For each PR created in step 4:

```bash
gh pr edit <number> --title "..." --body-file <tmpfile> --add-assignee @me
```

Skip PRs that already existed unless the user asked to refresh them, except for the
attribution block below: strip that from every PR the run touched, refreshed or not. Leave
the temp directory where it is: an `rm -rf` outside the repo can raise a permission prompt
and stall the run, and `mktemp -d` gave the run a path of its own that nothing else will
collide with.

**Always assign, in both modes.** `gh stack submit` leaves a PR unassigned, so it shows up
in nobody's list of work to chase. Use `@me` rather than a login: it resolves to whoever
authenticated `gh`, which is the person who opened the PR, and keeps the skill portable.

**Drop the CLI attribution, keep anything a person or a bot wrote.** The body is not empty
when `submit` creates it. It holds the auto-generated prose from the commits, a `---`
separator, and a `<sub>Stack created with GitHub Stacks CLI</sub>` line. None of that is
worth keeping: the prose is superseded by the body drafted in step 2, and the `<sub>` line
is attribution and a feedback link, not stack navigation. Navigation comes from the stack
object `submit` creates on GitHub, which the web UI renders whether or not the line is
there.

The separator is worse than clutter. `submit` appends it directly under the last line of
prose, and a `---` on the line after a paragraph is a setext heading in GitHub Markdown,
so the closing paragraph renders as a giant bold title. Delete the separator and the
`<sub>` line together, as one block:

```
---

<sub>Stack created with <a href="https://github.com/github/gh-stack">GitHub Stacks CLI</a> • <a href="https://gh.io/stacks-feedback">Give Feedback 💬</a></sub>
```

`submit` re-appends this on every run, so a body written before or during step 4 gets it
back. Strip it after the last `gh stack submit` of the run, and check it is gone rather
than assuming the edit took:

```bash
gh pr view <number> --json body --jq .body | grep -c 'gh-stack'   # expect 0
```

The same applies after `pr:sync` or any later `submit` on an existing PR: the block
returns and the heading breakage returns with it.

Review bot blocks fenced in `<!-- -->` are the exception, in both modes. Those are
somebody's output and a plain `--body-file` destroys them, which no later `submit` or
`sync` undoes.

Do not assume a position for any of these. The generated layout has varied between
versions, so find the blocks rather than slicing by line number:

```bash
mktemp -d                                                  # use the printed path as <dir>
gh pr view <number> --json body --jq .body > <dir>/body.old
grep -n '<!--' <dir>/body.old                              # bot blocks, if any
gh pr edit <number> --body-file <dir>/body.new             # no bots: the draft alone
```

With bot blocks present, append them below the draft and check they survived:

```bash
gh pr view <number> --json body --jq .body | grep -c '<!--'
```

One directory per run, and paste its literal path into the commands that follow: each of
these runs in its own shell, so a `$dir` variable is empty by the second line. Fixed
`/tmp/body.*` names are shared with every other run on the machine, and losing that race
puts one PR's prose on another.

### 6. Report

One line per PR, bottom to top, with number, URL, and state. If drafts, add how to flip
them: `gh pr ready <number>`. If the push succeeded but a PR failed, say so explicitly so
the user knows the branch is published but unraised.

## Landing the work

Deliberately manual in both modes. `gh pr merge` works on a single PR but not on stacked
PRs at all; a stack lands with `gh stack merge --yes`, bottom to top, all or nothing. No
skill here drives either, because merging is the step in this workflow with the least
recoverable outcome. Tell the user the command and let them run it.

## Example

User: "put these up as PRs." `gh stack view --json` shows three layers on trunk `main`
and no PRs yet. Titles and bodies are drafted from each layer's commits, previewed as
drafts, and confirmed.

```
$ gh stack submit --auto
Checking stack state...
Pushing to origin...
✓ Created PR #1 for config
✓ Created PR #2 for store-get
✓ Created PR #3 for user-handler
✓ Stack created on GitHub with 3 PRs (stack #4)
✓ Pushed and synced 3 branches
```

Each base points at the layer below, which is the property to check:

```
$ gh pr list --json number,baseRefName,headRefName,isDraft
#1 draft=true  config       -> main
#2 draft=true  store-get    -> config
#3 draft=true  user-handler -> store-get
```

Then `gh pr edit` on each, replacing the generated body with the drafted one and assigning
yourself, and report:

```
#1 https://github.com/owner/repo/pull/1  draft  config
#2 https://github.com/owner/repo/pull/2  draft  store-get
#3 https://github.com/owner/repo/pull/3  draft  user-handler

Un-draft with: gh pr ready <number>
Landing the stack is manual: gh stack merge --yes
```

The same work on one branch is one push and one create, and nothing to strip afterwards:

```
$ git push -u origin HEAD && gh pr create --draft --base main \
    --title "Add the user endpoint handler" --body-file /tmp/x/body.md --assignee @me
https://github.com/owner/repo/pull/1
```

## Failure modes

**Exit 9, stacked PRs unavailable.** Rare, since the feature is in public preview. Report
it and stop. Do not collapse the layers into one PR; that discards the work `pr:commit`
did.

**Exit 4, GitHub API failure.** Check `gh auth status` and retry once. Do not rewrite the
command.

**A push is rejected.** In stack mode `submit` is not atomic, so earlier branches may
already be pushed; fix the rejected branch and rerun the same command, which is safe to
repeat. In single mode a rejection means the remote branch moved, which is `pr:sync`, not
a `--force` away.

**`pull request already exists` from `gh pr create`.** The branch has an open PR. Push to
update it and edit the body if asked, rather than opening a second one.

**Every PR in the stack is already merged.** `submit` forks the unmerged branches into a
new stack rooted at trunk. Expected, not an error. Say it happened.

**Never** force-push, merge, approve, or pass `--reviewer` or `--label` unless the user
asked. CODEOWNERS usually handles reviewers. Self-assignment is the exception and is
standing policy, covered in step 5.
