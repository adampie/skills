# Pull request titles and bodies

The same rules for a single pull request and for every layer of a stack. In a
stack, each layer gets its own title and body written against its own diff: a
body describing the whole stack, repeated three times, tells a reviewer nothing
about the PR in front of them.

Read the branch before writing. For a single PR that is
`git log <trunk>..<branch>` and its diff; for a layer it is
`git log <layer below>..<layer>`.

## Title

Imperative, stands alone in a merged history, under ~70 characters.

A single-commit PR usually wants the commit subject as its title. Do not
paraphrase it into something vaguer.

### The Linear ticket

Work driven by a Linear ticket carries its ID in the title, even in a repo that
prefixes nothing: `INF-318: Rotate the Atlantis deploy key`. Sources, in order:
the ticket this session has been working from, the branch name
(`adampie/inf-318-rotate-deploy-key`, uppercased), then the commits. Use the ID
only when one of those states it; a ticket mentioned in passing is not the
ticket this branch implements, and an invented ID points a reader at someone
else's work.

Every layer of a stack carries the same prefix. One prefix at most: a repo that
already prefixes with the same ID does not get it twice.

### Repos that enforce a title format

A Conventional Commits or semantic-release check rejects `INF-318:` outright,
so look before writing:

```bash
find . -maxdepth 1 \( -name 'commitlint.config.*' -o -name '.commitlintrc*' \
  -o -name '.releaserc*' -o -name 'release-please-config.json' \)
grep -rlE 'semantic-pull-request|commitlint|semantic-release|release-please' .github/workflows 2>/dev/null
```

`find` rather than `ls` with those globs: zsh aborts the whole command on an
unmatched glob, so the `ls` form checks none of the paths, including the ones
that exist.

Either hit, or a repo whose own PR titles are uniformly conventional, means the
enforced format wins and the ticket moves to the end:
`feat(api): rotate the deploy key (INF-318)`. Drop it to its own line in the
body when that breaks the length limit the check imposes.

## Body

Why first, in one or two sentences, then what changed as one-line bullets.
British English, no em-dashes, no hype.

- **Aim for 100 words and stop at 200.** A reviewer should take it in without
  scrolling. Past that, reviewers skim and the detail is wasted anyway.
- **Cut anything the diff already says.** No file-by-file walkthrough, no
  narrating a rename, no "added a test" beside a visible test file.
- **Delete any sentence that would be true of a different PR.** "Improves
  reliability" and "follows best practice" pass no such test. Neither does a
  sentence explaining why the change matters in general terms.
- **No headings under 200 words.** On a short body they are decoration. Three
  or more genuine sections earn them.
- **Backticks only for text the reader would type:** a command, a flag, a path.
  Not skill names, not concepts, not ordinary words that happen to name a tool.
  Monospace breaks the line visually, so a body where every third phrase is
  grey reads worse than one with none. Write "there is no push skill", not
  "there is no `push` skill". At most five spans and one code block; past that,
  cut the ones naming things rather than text to type.
- **Link rather than retell.** Point at the commit, issue, or run. Detail
  belongs in commit messages, and repeating it in the body means two copies to
  keep in step.
- **Limitations,** one line, when a reader would otherwise be surprised.
  Honest beats complete.
- **Proof,** one line, only if there was a real run. Never pad with "it
  compiles" or "lint is clean". No proof is better than manufactured proof.
- **No process narration and no tool attribution.** Not "This PR...", not
  "Claude has...", and no generated-with footer.

## Repository templates

If the repo has `.github/pull_request_template.md`, map the text into its
headings, strip the HTML comments, and leave checkboxes unticked for the user.
Adopt the format, keep the voice. A heading is not a quota, and an empty
section is better deleted than filled with a restatement.

Never emit a checklist of unticked boxes that the template did not ask for.

## Linking an issue

Use a closing keyword only when merging the PR should genuinely close the
issue: `Closes #12`, on its own line at the end. In a stack, put it on the
layer that finishes the work, not on every layer, or merging the bottom one
closes the issue while the rest is still in review.
