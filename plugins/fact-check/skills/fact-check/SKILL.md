---
name: fact-check
description: "Fact-checks factual claims against live web sources and against the local codebase, reporting each one with a verdict, a correction and a citation. Use when the user asks to fact-check or verify a document, article, draft, README or design doc, to check whether a claim is true, to confirm that what the docs say about the code is still what the code does, to trace whether a stated behaviour holds by following the call paths, to source or back up statements, or to audit the accuracy of what Claude itself said earlier in the conversation. Not a code review: it checks claims made about the code, not the quality of the code."
compatibility: Requires WebSearch and WebFetch for external claims; Read, Grep, Glob and Bash for claims about a repository
metadata:
  author: adampie
  version: "0.2.0"
---

# Fact check

Extract every factual claim from a piece of text, verify each against live web
sources or against the code it describes, and report the findings inline:
verdict first, correction next to the claim, worst first.

Never answer from memory. A claim that looks obviously true still gets a search,
because the ones that feel settled are exactly where a stale detail survives.
For a claim about this repository, memory means anything read earlier in the
conversation and the document being checked. Open the file again.

Verifying takes as long as it takes. A claim about what the code does is worth
more searching than a claim about what a release note said, because the call
graph has more places to hide a second answer.

## Verdicts

Four values, not two. Collapsing to a bare true or false is the main way this
goes wrong: the interesting claims are true in substance and wrong in a detail.

| Mark | Verdict | Meaning |
| --- | --- | --- |
| `✓` | True | Sources agree with the claim as stated |
| `⚠` | Partly true | True only under a condition the claim omits, or true in substance with one detail wrong |
| `✗` | False | Sources state otherwise |
| `?` | No source | No adequate source found |

**Every verdict is as of today, and for a repo claim, as of the tree checked.**
A claim that held when it was written and has since been overtaken is `✗`,
exactly like one that was never true. Whether the author could have known is a
separate question from whether a reader can rely on it, and only the second is
what a fact-check answers. What changed, and when, goes in the correction line,
where it tells the reader what to write instead.

A comment or README that has drifted from the code is the same failure as a
stale statistic, and takes the same mark. "This was true before the refactor"
is not a verdict.

There is no verdict for "was true once". Reaching for a softer mark because the
claim used to hold leaves a false statement standing.

`?` is a real result, not a failure to try. Marking a claim false when a search
came back empty manufactures a finding out of absence.

## What counts as a claim

Check anything evidence could falsify: numbers, dates, attributions,
superlatives, causal assertions, quotations, and anything stated as current
fact.

Skip opinions, predictions, stipulated definitions, hypotheticals, and the
user's statements about their own intent. List what was skipped in one line.
Dropping a claim silently reads as endorsement.

**Split compound sentences.** "Rust was released in 2010 by Mozilla and reached
1.0 in 2015" is two claims taking two verdicts. One verdict over a compound
sentence hides which half is wrong.

Claims about a repository split the same way and further. "The reconciler runs
once every 24 hours from a cron" is three: that it runs on a daily period, that
a cron is what runs it, and that nothing else does. Those three fail
independently, and the third is the one a reader never thinks to check.

## Where the answer lives

The claim decides the evidence, not the document it appears in. A README
sentence about Postgres is a web claim; a blog post describing this service's
retry policy is a repo claim.

| Claim is about | Evidence |
| --- | --- |
| The world outside the repo | Web search |
| This repository's code, config, schema or behaviour | The files themselves |
| A dependency's behaviour | Its source at the version the lockfile pins, then its docs |
| History: when something changed, who changed it, what shipped | `git log`, `git blame`, tags |
| Both | Both, and say in the correction which one settled it |

The dependency row is where this goes wrong quietly. Published docs describe
the current release, the lockfile pins an older one, and a claim checked against
the docs gets `✓` for behaviour the installed version does not have. Read the
pinned version.

State which tree the check speaks for before starting: the default branch, or
the working tree including uncommitted changes. They differ, and a claim can be
true in one and false in the other.

## Steps

### 1. Identify the text and extract the claims

| Asked for | What to check |
| --- | --- |
| A document, file or pasted article | Read it in full first, then extract |
| "fact-check what you just said" | Claude's previous message, quoted from the transcript |
| "fact-check this conversation" | Statements of fact from both sides, Adam's included |
| A single typed claim | That claim alone |
| A README, design doc or ADR in the repo | Read it in full, then route each claim by the table above |
| "check the docs still match the code" | Every behavioural claim the doc makes, traced to the code |
| A comment or docstring | The claim it makes, against the function it sits on |

Quote each claim verbatim. Paraphrasing while extracting is how a claim gets
checked in a weaker form than it was made.

State the count before gathering anything, split by where each claim will be
settled. A long document is dozens of searches, so if the web count runs past
roughly fifteen, say so and confirm the scope first.

Repo claims are not counted against that threshold. A trace costs more than a
search and is worth more, so the answer to a large number of them is to take
longer rather than to sample. Confirm scope only when the trace would span
repositories that are not checked out.

### 2. Gather evidence, one claim at a time

#### Web claims

**Query in neutral terms. Do not paste the claim into the search.** Search
"Rust 1.0 release date", never "Rust 1.0 was released in 2015, wasn't it".
Results are summarised by a model that leans toward agreeing with the framing
it was handed; a loaded query gets "your details check out" for a claim that
needed a caveat.

- **Disambiguate a shared name first.** "Rust" alone returns the language, the
  video game and RustDesk. Establish which entity the text means, then search.
- **Establish the current state, not the original one.** Add the current year to
  the query. "Is the largest", "has never", "still", "currently", and any verb
  in the present tense are claims about today and are checked against today.
- **Search for what superseded it.** For anything versioned, ranked, priced or
  regulated, a source confirming the claim is not enough; find the latest
  position before marking `✓`. The first result is often the announcement that
  was current when the text was written.
- **Anchored past-tense claims are judged on their own terms.** "Linux gained
  Rust support in 6.1" is a fact about 2022 and stays `✓` however far the kernel
  has moved since. "Rust support in Linux is experimental" is a claim about now.
- **Search again when the first pass is thin** or returns only content farms.
  One weak search does not justify `?`.

#### Repo claims

**Grep for the symbol, never for the claim's wording.** Searching the codebase
for "every 24 hours" finds the comment that repeats the claim. Searching for
the function name finds what actually calls it. A doc and the comment it was
copied from are one source counted twice.

- **Find the definition, then enumerate every reference.** One call site
  matching the claim proves nothing; the claim is usually falsified by a
  second one. This is the repo form of "search for what superseded it", and it
  is the single rule this whole section exists for. Stop when the references
  are exhausted, not when one fits.
- **Follow the path to where the behaviour is decided.** A claim about how
  often, how many, or under what condition is settled by the scheduler entry,
  the loop bound, the guard clause or the retry policy, not by the function the
  claim names. Read the wrapper as well as the callee.
- **Check the negative claim hardest.** "Only", "never", "always" and "the
  single" are exhaustiveness claims, and confirming one instance does not
  touch them. They are settled by a search that comes back empty, so the
  search has to be one that would have found the counterexample.
- **Widen the search when the first grep is thin.** A symbol renamed since the
  doc was written, or reached through an alias, returns nothing. Nothing found
  is `?` only after searching for what the thing was called before.

Read `references/code.md` before settling any of this: it lists where a
reference hides when grep finds only one, what decides a frequency claim
besides the schedule, how to date a change, and what the repo cannot answer.

### 3. Rank the sources

Prefer the primary record over anything written about it: the release
announcement, the filing, the paper, the mailing list thread, the statistical
release. When search surfaces only commentary, WebFetch the primary source it
cites and read that instead.

**On conflict, the primary source settles it. Never average two answers.** In
the trial one source placed Rust support in Linux 5.19, where it had been
expected, and another in 6.1, where it actually landed. The kernel mailing list
resolves that; splitting the difference invents a third wrong answer.

**In a repository the code is the primary record.** Everything else describes
it and can be wrong about it, in this order: source, then the config and
manifests that parameterise it, then tests, then comments and docstrings, then
prose docs, then commit messages and PR descriptions. Where two disagree, the
lower rank is the finding, not the evidence.

Tests sit above comments because a passing test is executed and a comment is
not, and below config because a test asserts what someone wanted rather than
what production runs. A skipped or `xfail` test asserts nothing.

**Independence matters.** A survey result cited to the blog of the language it
flatters is the claimant repeating itself. Find a source that does not share an
interest with the claim. The same trap in a repo: a doc, the comment it was
written from, and the commit message that announced both are one source, and
none of them is the code.

**Only cite what was actually returned.** Never reconstruct a plausible URL from
memory, and never cite a line number without opening the file at it.
`references/sources.md` ranks source types by domain.
`references/code.md` covers tracing a claim through a codebase.

### 4. Report inline

The reader's question is "which of these is wrong", so answer that first.

**Order by severity, not by position in the text:** `✗`, then `⚠`, then `?`,
with every `✓` collapsed into a run at the end. Quote each claim verbatim so it
stays findable in the original.

**Lead with the subject, then the claim quoted.** Verbatim quoting on its own
produces fragments: "which reads the manifests", "so it can run online audits",
"the last two". Each is exactly what the text said and none can be read alone.
Name the file, command or symbol the claim is about, outside the quotation
marks, then quote the claim as written. The subject makes it readable, the
quote keeps it findable in the original.

**One entry per block, separated by a blank line**, including between `✓`
entries. The run at the end is where a reader looks up a claim by name, and a
wall of them defeats that.

**Depth follows the verdict.** A `✓` is one line: mark, subject, claim, source.
Anything else puts the correction on the line below, and a further line only
where the verdict is not self-evident from the correction. Continuation lines
indent to the subject.

```
✗ `subject` "the claim, quoted"
   What is actually the case. source.example.com

⚠ `subject` "the claim, quoted"
   The correction, naming the omitted condition. source.example.com
   Why the claim is wrong in the way it is wrong.

✓ `subject` "the claim, quoted"   source.example.com
```

**Cite a repo claim as `path:line`**, at the line that decides the behaviour
rather than the line the claim names. A claim about how often a job runs cites
the schedule, not the function. Where several files settle one claim, cite each,
because the reader has to change all of them.

Write the correction as a statement of fact, not as commentary about the claim.
"15 May 2015" beats "this date is incorrect", which makes the reader go looking
for the right answer. For a repo claim that means naming the actual behaviour:
"also called from `POST /admin/reconcile`" beats "there is another caller".

Reserve the third line for `⚠` and `?`, where the correction alone does not
show why the verdict is what it is: which condition the claim drops, or what was
searched and not found. On a `✗` the correction is the reasoning, and a third
line only restates it.

**Where a claim has been overtaken, date the change in the correction.** "Since
March 2025, X" tells the author what to write; "this is now out of date" makes
them go and find out.

Close with a tally and the date the check speaks for:

```
5 claims: 3 true, 1 partly true, 1 false. Checked 4 August 2026.
```

Count in the verdict order above and drop any category holding nothing. A run
with an unsourced claim reads `... 1 no source, 2 false`.

Put the tally first instead when there are more than five claims. The date
matters because a verdict on a present-tense claim expires, and a report read
six months from now should say what it was current against.

**A report covering repo claims names the tree as well as the date**, because
that is what its verdicts expire against:

```
4 claims: 1 partly true, 2 false, 1 no source.
Checked against main at a1b2c3d, 4 August 2026.
```

Say so explicitly when the check ran against uncommitted changes, since nobody
else can reproduce it.

## Example

Input: "Rust was first released in 2016 by Mozilla and reached version 1.0 in
2015. Its borrow checker eliminates data races at compile time. Rust has been
the most loved language in the Stack Overflow survey every year since 2016, and
its support in the Linux kernel remains experimental."

Six claims, each searched neutrally: "Rust programming language first release
history", "Rust 1.0 release date", "Rust borrow checker data race guarantees
unsafe limitations", "Stack Overflow developer survey most admired language
history", "Linux kernel Rust support status 2026".

```
✗ Rust "was first released in 2016"
   2010: announced at the Mozilla Annual Summit, initial git commit
   16 June 2010. blog.rust-lang.org

✗ Rust in Linux "remains experimental"
   The experimental label was removed in Linux 7.0 (June 2026), after the
   2025 Maintainers Summit concluded the experiment. Rust is now
   officially supported. lkml.org

⚠ the borrow checker "eliminates data races at compile time"
   True of safe Rust only. `unsafe` permits raw pointer dereference and
   the checker cannot see across FFI boundaries; both reintroduce data
   races. doc.rust-lang.org
   The guarantee is conditional on every `unsafe` block and FFI binding
   upholding its obligations. "Eliminates" states it unconditionally.

⚠ Stack Overflow survey "most loved language ... every year since 2016"
   Still top in 2025 at 72%, but the category was renamed "most admired"
   in 2024. survey.stackoverflow.co
   The streak is real; the label no longer exists. Sources also disagree
   on the start year, the Rust blog dating it to 2015 against the 2018
   survey calling itself the third year running.

✓ Rust "by Mozilla"   blog.mozilla.org

✓ Rust "reached version 1.0 in 2015"   blog.rust-lang.org

6 claims: 2 true, 2 partly true, 2 false. Checked 4 August 2026.
```

Two things this example turns on. "By Mozilla" is split off from the release
year, because one half of that sentence is wrong and the other is right, and a
single verdict over both would lose it. And the Linux claim is `✗` rather than
anything softer: it was accurate for three years, which changes nothing for
someone about to publish it today.

`references/code.md` works the same example through a repository, where a doc
claims a job runs once a day and every individual artifact agrees with it.

## Failure modes

**A verdict with no search behind it.** The tell is a verdict citing no URL.
Every claim gets its own search, including the ones that seem obvious.

**Content farms in the results.** Searching "Rust 1.0" surfaced `rustcasino.com`
and `corrosion-expert.com`. Domains built for search traffic restate each other
and are frequently model-generated. Discard and search again rather than
citing one.

**The search summary agreeing with the question.** Caught by neutral phrasing in
step 2. If a summary opens by confirming the premise it was given, verify
against the underlying source before accepting it.

**Padding a `✓`.** "This checks out", "the date matches exactly" and similar
add a line saying what the mark already said. A true claim is one line.
The saved space is what makes the wrong claims stand out.

**Near-miss numbers.** 83% against 85% is a wrong figure, not a rounding.
Report the source's number alongside the claim's and mark it `⚠`.

**Confirming a claim from the source that was current when it was written.**
The commonest way a stale claim passes: search returns the original
announcement, it matches word for word, and nothing prompts a check for what
replaced it. Anything versioned, ranked, priced or regulated needs the latest
position found before `✓`.

**Excusing a claim because it used to be true.** "This was correct at the time"
is not a verdict. The author is about to publish it now.

**Nothing checkable in the text.** Say so plainly and stop. An argument, a
proposal or a set of preferences has no factual surface, and inventing claims to
check produces filler.

**Stopping at the first matching call site.** The repo equivalent of confirming
a claim from the announcement that was current when it was written, and the
commonest way a repo claim passes wrongly. The cron exists, so "from a cron"
looks settled, and the admin route is never looked for. An exhaustiveness claim
is only ever settled by an exhausted search.

**Citing a comment as evidence for a doc.** Both were written by the same person
in the same commit, and neither is executed. Verify against the code, then treat
the stale comment as a second finding.

**A verdict with no `path:line` behind it.** The repo form of a verdict citing
no URL. If the trace did not end at a specific line, it did not end.

**Reading the published docs for a pinned dependency.** The docs describe the
current release; the lockfile pins something older. Read the version installed.

**Marking deployed state `✓` from a manifest.** The repo can show what would be
applied, not what is running. Environment variables, feature flag values, cluster
state and anything set at runtime are `?` unless the repo pins them.

**Treating a claim about the code as a bug report.** The job is to say whether
the sentence is accurate, not whether the behaviour is correct. A paging limit
that contradicts the doc is a false claim; whether 500 is the right number is
not this skill's question. Note it in one line and move on.
