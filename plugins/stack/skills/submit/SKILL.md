---
name: submit
description: "Push a stack of branches and create or update their pull requests on GitHub, using gh stack submit. Use when the user says submit the stack, open the PRs, raise these for review, push this up, put these up as PRs, or mark them ready. Opens one draft pull request per layer, each based on the layer below. Does not commit, which stack:commit does, and never merges."
compatibility: Requires gh 2.0+ with the github/gh-stack extension v0.1.0
metadata:
  author: adampie
  version: "0.1.0"
  tested-against: gh-stack v0.1.0
---

# Submit

Push every branch in the stack and open or update one pull request per layer, each based
on the layer below. Making the layers is `stack:commit`.

## Refuse first

| Condition | Check |
| --- | --- |
| Not a git repo | `git rev-parse --is-inside-work-tree` fails |
| No stack | `gh stack view --json` fails or lists no branches |
| No remote | `git remote` is empty |
| On the trunk | current branch equals the stack's `trunk` |
| Not authenticated | `gh auth status` fails |

A dirty working tree is a warning, not a refusal: say the uncommitted changes will not be
in the PRs and suggest `stack:commit`, then continue with what is committed.

## Steps

### 1. Read the stack

`gh stack view --json`. Record `trunk`, and each branch with its `pr` and `isMerged`.
Branches without a `pr` are the ones that will be created.

Note: v0.1.0 does not emit a `head` field per branch, whatever older docs show. Do not
parse one.

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
renaming the layer, which `stack:commit` covers, and hand-editing `.git/gh-stack`.

### 2. Draft the titles and bodies

`gh stack submit` has no title or body flag. It auto-generates from commits, so write the
real text now and apply it with `gh pr edit` in step 5.

For each layer, read `git log <base>..<branch>` and its diff, then write:

- **Title:** imperative, stands alone in a merged history, under ~70 characters. One
  prefix at most, and only if the repo already uses one (`INF-318:`, `feat(api):`). Take
  a ticket ID from the branch name or commits if there is one.
- **Body:** why first, in one or two sentences, then what changed as one-line bullets.
  British English, no em-dashes, no hype.
- **Backticks only for text the reader would type:** a command, a flag, a path. Not skill
  names, not concepts, not ordinary words that happen to name a tool. Monospace breaks the
  line visually, so a body where every third phrase is grey reads worse than one with
  none. Write "there is no push skill", not "there is no `push` skill".
- **Aim for 100 words and stop at 200.** A reviewer should take it in without scrolling.
  Past that, reviewers skim and the detail is wasted anyway.
- **Cut anything the diff already says.** No file-by-file walkthrough, no narrating a
  rename, no "added a test" beside a visible test file.
- **Delete any sentence that would be true of a different PR.** "Improves reliability"
  and "follows best practice" pass no such test. Neither does a sentence explaining why
  the change matters in general terms.
- **No headings under 200 words.** On a short body they are decoration. Three or more
  genuine sections earn them.
- **Link rather than retell.** Point at the commit, issue, or run. Detail belongs in
  commit messages, and repeating it in the body means two copies to keep in step.
- **Limitations,** one line, when a reader would otherwise be surprised. Honest beats
  complete.
- **Proof,** one line, only if there was a real run. Never pad with "it compiles" or
  "lint is clean". No proof is better than manufactured proof.

If the repo has `.github/pull_request_template.md`, map the text into its headings, strip
the HTML comments, and leave checkboxes unticked for the user. Adopt the format, keep the
voice. A heading is not a quota.

### 3. Preview and confirm

Opening PRs notifies reviewers and starts CI, so show the plan and wait for a go-ahead:

```
Stack: auth -> api-routes -> ui   (base: main)
Mode:  DRAFT                      (say "ready" to open for review)

  1. auth        Add token verification middleware
  2. api-routes  Add the user routes behind the new middleware
  3. ui          Add the dashboard that reads the user routes
```

Default to draft. Open ready only when the user asks.

### 4. Submit

```bash
gh stack submit --auto          # add --open only when the user asked for ready
```

`--auto` is required. Without it the command prompts for a title per PR and hangs. Add
`--remote <name>` if the repo has several remotes.

Stacked PRs are in public preview, so treat availability as given. Expect exit 0 and one
PR per unmerged layer, with each base pointing at the layer below.

### 5. Apply the real titles and bodies

For each PR created in step 4:

```bash
gh pr edit <number> --title "..." --body-file <tmpfile> --add-assignee @me
```

Skip PRs that already existed unless the user asked to refresh them. Delete the temp
files afterwards.

**Always assign.** `gh stack submit` leaves a PR unassigned, so it shows up in nobody's
list of work to chase. Use `@me` rather than a login: it resolves to whoever authenticated
`gh`, which is the person who opened the stack, and keeps the skill portable.

**Preserve what is already in the body.** It is not empty when `submit` creates it: it
carries a `<sub>Stack created with GitHub Stacks CLI</sub>` footer, which is what gives
readers stack navigation, and review bots may have appended blocks fenced in `<!-- -->`. A
plain `--body-file` replaces the lot, and a later `submit` or `sync` does **not** put them
back.

Despite reading as a footer, the `<sub>` block is the **first** line of the body, with any
bot blocks after it. Do not go looking for it at the end. Read the current body, then
prepend your prose and a blank line, keeping everything else in the order it was in:

```bash
gh pr view <number> --json body --jq .body > /tmp/body.old
{ cat /tmp/body.new; echo; cat /tmp/body.old; } > /tmp/body.final
gh pr edit <number> --body-file /tmp/body.final
```

Afterwards, confirm the footer survived: `gh pr view <number> --json body --jq .body |
grep -c 'Stacks CLI'` should print at least 1.

### 6. Report

One line per PR, bottom to top, with number, URL, and state. If drafts, add how to flip
them: `gh pr ready <number>`. If the push succeeded but a PR failed, say so explicitly so
the user knows the branches are published but unraised.

## Landing the stack

Deliberately manual. `gh stack merge --yes` merges the whole stack bottom to top, all or
nothing, and `gh pr merge` does not work on stacked PRs at all. No skill here drives it,
because merging is the step in this workflow with the least recoverable outcome. Tell the
user the command and let them run it.

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

Then `gh pr edit` on each, prepending the prose above the `<sub>` footer and assigning
yourself, and report:

```
#1 https://github.com/owner/repo/pull/1  draft  config
#2 https://github.com/owner/repo/pull/2  draft  store-get
#3 https://github.com/owner/repo/pull/3  draft  user-handler

Un-draft with: gh pr ready <number>
Landing the stack is manual: gh stack merge --yes
```

## Failure modes

**Exit 9, stacked PRs unavailable.** Rare, since the feature is in public preview. Report
it and stop. Do not collapse the layers into one PR; that discards the work
`stack:commit` did.

**Exit 4, GitHub API failure.** Check `gh auth status` and retry once. Do not rewrite the
command.

**A push is rejected.** `submit` is not atomic, so earlier branches may already be
pushed. Fix the rejected branch and rerun the same command; it is safe to repeat.

**Every PR in the stack is already merged.** `submit` forks the unmerged branches into a
new stack rooted at trunk. Expected, not an error. Say it happened.

**Never** force-push, merge, approve, or pass `--reviewer` or `--label` unless the user
asked. CODEOWNERS usually handles reviewers. Self-assignment is the exception and is
standing policy, covered in step 5.
