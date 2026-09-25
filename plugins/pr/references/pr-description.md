# Pull request titles and bodies

The same rules for a single pull request and for every layer of a stack. In a
stack, each layer gets its own title and body written against its own diff: a
body describing the whole stack, repeated three times, tells a reviewer nothing
about the PR in front of them.

Read the branch before writing. For a single PR that is
`git log <trunk>..<branch>` and its diff; for a layer it is
`git log <layer below>..<layer>`.

## Title

Imperative, stands alone in a merged history, under ~70 characters. One prefix
at most, and only if the repo already uses one (`INF-318:`, `feat(api):`). Take
a ticket ID from the branch name or the commits if there is one.

A single-commit PR usually wants the commit subject as its title. Do not
paraphrase it into something vaguer.

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
  "there is no `push` skill".
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
