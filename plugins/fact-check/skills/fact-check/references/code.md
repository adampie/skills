# Tracing a claim through a codebase

The rule from `SKILL.md` is that the code is the primary record and everything
else describes it. This file covers the two things that rule does not settle:
where a reference hides when grep says there is only one, and which claims the
repo cannot answer at all.

## What settles which claim

| Claim of the form | Settled by | Not settled by |
| --- | --- | --- |
| "runs every N" | The scheduler entry: crontab, CronJob, timer unit, Actions `schedule`, beat config | The function's name or its docstring |
| "is called once" | Every reference to the symbol, plus the retry and concurrency policy around it | The one call site that matches |
| "only X can do Y" | A search that would have found a counterexample, returning none | Any number of confirming examples |
| "returns / always sets" | The function's exits, including early returns and the error path | The happy path |
| "is validated" | The guard actually on the path taken, not a validator defined nearby | A validator existing in the file |
| "defaults to X" | The resolution order: literal, config file, environment, flag | The literal in the signature |
| "is atomic / transactional" | The transaction boundary, and whether the call sits inside it | A `BEGIN` somewhere in the module |
| "N per second / N rows" | The limit constant and the loop that applies it | A constant named `LIMIT` |
| "we no longer use X" | A search for X returning nothing outside dead code | The replacement existing |

## Where a call site hides

Grep for a symbol finds direct calls. These are the references it misses, and
any one of them falsifies an "only" or "once".

- Re-exports and aliases: `export { reconcile as run }`, barrel files,
  `from x import y as z`.
- Indirect invocation: passed as a callback, stored in a handler map, resolved
  from a DI container, registered by a decorator, dispatched by string name.
- Framework convention: file-based routing, naming conventions that bind a
  handler without any call appearing, lifecycle hooks, migrations run by
  directory order.
- Reflection and metaprogramming: `getattr`, `method_missing`, dynamic imports,
  anything assembling a symbol name from a string.
- Generated code, and the generator's templates.
- Non-code entry points: HTTP routes, queue consumers, event subscriptions,
  webhook targets, CLI subcommands, scheduled tasks, database triggers.
- Other repositories, when the symbol is exported from a published package.
  This is `?` territory, since the repo cannot show who imports it.

When a symbol is public API, say so in the correction. "Only called from the
cron within this repo" is a different and weaker claim than "only called from
the cron", and the difference is the one the reader needs.

## Schedule and frequency claims

"Once every 24 hours" is false in more ways than the schedule expression. Check
each before marking `✓`:

- Retries: `backoffLimit`, `restartPolicy`, application-level retry wrappers,
  queue redelivery.
- Concurrency: `concurrencyPolicy: Allow` permits overlap; replica count above
  one runs the same schedule per instance unless something elects a leader.
- Fan-out: a daily job looping over tenants calls the inner function once per
  tenant, so "runs daily" and "is called once daily" are different claims.
- Timezone and DST: a daily cron is not every 24 hours across a DST boundary,
  and a `TZ`-less cron runs in the cluster's zone rather than the author's.
- Suspension and flags: `suspend: true`, a feature flag wrapping the body, a
  commented-out schedule, an early return on an environment check.
- Manual triggers: admin endpoints, `kubectl create job --from=cronjob`,
  runbook steps.
- Backfills: a separate path that calls the same function over a date range.

## What the repo cannot settle

These are `?`, and saying so is the correct result rather than a failure:

- Whether a manifest is applied, and to which environment.
- Values of environment variables, secrets and runtime feature flags.
- The behaviour of an external service the code calls.
- Which branch a data-dependent condition takes in production.
- Load, timing, and anything else that depends on production data volume.
- Whether the deployed image matches the current default branch.
- Who calls an exported symbol from outside the repo.

Where infrastructure lives in another repository, say which claim it would
settle and where it would be. "Not in this repo" is a more useful `?` than
"could not determine".

## Using history

`git log -S "<symbol>"` finds the commits that added or removed a use, which is
how a correction gets to name when a claim stopped being true. `git blame` on
the deciding line gives the same answer for a value that changed. Date the
change in the correction the same way as for a web claim: "the second caller
was added in March 2026" tells the author what happened; "this is out of date"
does not.

A commit message is evidence of intent, not of behaviour, and ranks below the
diff it describes. Where they disagree, the diff wins and the message is a
second finding.

## A worked example

Input, from a design doc: "The reconciler runs once every 24 hours from a cron,
so a stale row can be at most a day old."

Four claims. The trace: locate `reconcile` and read it, list every reference to
it rather than stopping at the cron, read the manifest that schedules it, and
read the loop that decides how much one run gets through.

```
✗ `reconcile` "from a cron"
   Also called by POST /admin/reconcile, which invokes it directly with
   no scheduling in between. src/routes/admin.ts:88, src/jobs/reconcile.ts:12

✗ `reconcile` "a stale row can be at most a day old"
   Each run pages 500 rows per tenant and returns. A tenant above that
   carries the remainder into the following day, without bound.
   src/jobs/reconcile.ts:41

⚠ `reconcile` "runs once every 24 hours"
   Scheduled 0 3 * * * , so daily, but backoffLimit is 6 under
   restartPolicy OnFailure. k8s/cron/reconcile.yaml:9
   Once a day holds only for a run that succeeds. A failing day runs it
   up to seven times, and the doc's guarantee is what fails with it.

? the reconcile CronJob "runs" (that the job is live at all)
   The manifest does not set suspend, which defaults to false, but
   whether this manifest is applied to the production cluster is not
   determinable from the repo. k8s/cron/reconcile.yaml

4 claims: 1 partly true, 2 false, 1 no source.
Checked against main at a1b2c3d, 4 August 2026.
```

What this example turns on. Every individual artifact reads as though the doc
were right: there is a cron, its schedule is daily, and `reconcile` is what it
calls. The claim fails on the things next to those artifacts, which is why the
rule is to enumerate references rather than confirm one. The `?` is the honest
result for deployed state: the repo holds the manifest, not the cluster, and
marking that `✓` would be citing an intention as a fact.

## Which tree

Verdicts are against a specific tree, so establish it before starting:
`git rev-parse --short HEAD` and `git status --porcelain`. A dirty tree means
the check cannot be reproduced from a commit, which the report has to say.
Where a claim is true on the default branch and false in the working tree, that
is the finding, and both belong in the correction.
