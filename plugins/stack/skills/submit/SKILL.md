---
name: submit
description: "Push a stack of branches and create or update their pull requests on GitHub, using gh stack submit. Use when the user says submit the stack, open the PRs, raise these for review, push this up, put these up as PRs, or mark them ready. Falls back to plain chained pull requests when the repository does not have stacked PRs enabled. Does not commit, which stack:commit does, and never merges."
compatibility: Requires gh 2.0+ and the github/gh-stack extension
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

### 2. Draft the titles and bodies

`gh stack submit` has no title or body flag. It auto-generates from commits, so write the
real text now and apply it with `gh pr edit` in step 5.

For each layer, read `git log <base>..<branch>` and its diff, then write:

- **Title:** imperative, stands alone in a merged history, under ~70 characters. One
  prefix at most, and only if the repo already uses one (`INF-318:`, `feat(api):`). Take
  a ticket ID from the branch name or commits if there is one.
- **Body:** why first, in a sentence or two, then a short what. British English, no
  em-dashes, no hype, no restating the diff file by file. Backticks only for exact
  commands or ambiguous paths.
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

**If it exits 9, stacked PRs are not enabled on the repository.** Fall back to plain
chained PRs, which give the same layered review without the GitHub stack object:

```bash
gh stack push                            # branches only, no PRs
# then bottom to top, basing each PR on the layer below:
gh pr create --base main       --head auth       --draft --title "..." --body-file f1
gh pr create --base auth       --head api-routes --draft --title "..." --body-file f2
gh pr create --base api-routes --head ui         --draft --title "..." --body-file f3
```

Say plainly that you fell back and why. Bases still chain, so reviewers still see one
layer per PR.

### 5. Apply the real titles and bodies

For each PR created in step 4, `gh pr edit <number> --title "..." --body-file <tmpfile>`.
Skip PRs that already existed unless the user asked to refresh them. Delete the temp
files afterwards.

### 6. Report

One line per PR, bottom to top, with number, URL, and state. If drafts, add how to flip
them: `gh pr ready <number>`. If the push succeeded but a PR failed, say so explicitly so
the user knows the branches are published but unraised.

## Example

User: "put these up as PRs."

1. `gh stack view --json` shows `auth -> api-routes -> ui` on trunk `main`, no PRs.
2. Draft three titles and bodies from each layer's commits.
3. Preview as draft, user confirms.
4. `gh stack submit --auto` creates #41, #42, #43 with chained bases.
5. `gh pr edit` on each to replace the auto-generated text.
6. Report the three URLs and `gh pr ready` to un-draft.

## Failure modes

**Exit 9, stacked PRs unavailable.** Use the chained-PR fallback in step 4. Do not
collapse the layers into one PR; that discards the work `stack:commit` did.

**Exit 4, GitHub API failure.** Check `gh auth status` and retry once. Do not rewrite the
command.

**A push is rejected.** `submit` is not atomic, so earlier branches may already be
pushed. Fix the rejected branch and rerun the same command; it is safe to repeat.

**Every PR in the stack is already merged.** `submit` forks the unmerged branches into a
new stack rooted at trunk. Expected, not an error. Say it happened.

**Never** force-push, merge, approve, or pass `--reviewer`, `--label`, or `--assignee`
unless the user asked. CODEOWNERS usually handles reviewers.
