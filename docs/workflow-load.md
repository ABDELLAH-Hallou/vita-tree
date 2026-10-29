# Reproducing workflow load

These tests measure Vita Tree orchestration using local, deterministic providers.
They do not measure provider capacity, model quality, hiring outcomes, or a
supported maximum number of applications. No live provider is contacted.

## Profiles and gates

[`load_profiles.json`](../tests/fixtures/load_profiles.json) is the versioned,
MIT-licensed definition. Budgets were declared before running the profiles.
The reference environment is Ubuntu 24.04, Python 3.12 and Chromium, with an
explicit TeX Live installation for the real-PDF profile. Machine details,
fixture/code hashes, versions and declared concurrency accompany each result.
Do not silently widen a budget to make a slow run pass; version and explain a
deliberate change. Other operating systems can run the same scenarios, but are
not interchangeable timing baselines.

CI runs the sustained profile on three independent runner instances. Each sample
is measured against the same budgets; passing samples do not average away misses.
Reports identify the replica, CPU model, kernel and available resources.

| Profile | Simultaneous branches | Waves | Existing runs / branches | Provider sleep per step | Poll clients |
| --- | ---: | ---: | ---: | --- | ---: |
| `ci` | 3 | 2 | 250 / 24 | 150, 250, 350 ms | 2 |
| `sustained` | 6 | 5 | 2,000 / 64 | 300, 450, 600 ms | 3 |

Half the seeded history has requirement-revision bindings; one fifth has
resolved factual-review metadata. These are synthetic metadata histories, not
thousands of complete CV/report/checkpoint bodies. The source includes a local
included file. Additional scenarios exercise repeated Cover failure and retry,
external include edits, unrelated draft saves, connection removal, clean
worktree release, graceful shutdown, abrupt server death and recovery.

The archived requirement bindings share one synthetic approved definition.
Histories dominated by distinct, large approval records are not represented;
the bounded per-refresh capture falls back to fresh reads for those records.

The measured preparation subset is Extract → Analyze → Adapt → Cover, followed
by validation/publication. Human decision time and AI Review throughput are not
measured by these profiles. The API still returns the full history; archives
beyond the declared sizes and concurrency are not qualified by these results.

The scenario controller additionally polls one run at a time, waiting 30 ms
after each response while awaiting completion. Those probes are included in the
API/resource evidence; this is additional test-driver load, not normal browser
behavior. The browser profiles use the application's natural polling interval.

Measured, sanitized results (including failed budgets) are retained in
[`benchmarks/workflow-load.json`](benchmarks/workflow-load.json). Runs on separate
CI hosts are descriptive observations, not statistically controlled effect sizes.

| Budget | `ci` | `sustained` |
| --- | ---: | ---: |
| Submit p95 | 5 s | 10 s |
| History poll p95 | 1.5 s | 2.5 s |
| Local orchestration p95 | 8 s | 15 s |
| Restricted PDF call p95 | 15 s | 20 s |
| Shutdown | 10 s | 10 s |
| Server peak RSS / growth | 512 / 128 MiB | 768 / 192 MiB |
| Peak descendants / handle growth | 32 / 64 | 64 / 96 |
| Browser interaction p95 / JS heap | 200 ms / 128 MiB | 250 ms / 192 MiB |

Both profiles require zero unexpected failures, executing orphans and leaked
clean, owned worktrees. Expected provider failures, conflicts and interrupted
runs remain in the evidence. Passing safety checks with an exceeded performance
budget is not a performance pass.

On shared CI, only the sustained **orchestration p95** target is advisory, using
`--enforce-budgets --advisory-orchestration`. That flag does not change the target
or measured result. API/PDF/UI latency, shutdown, resource and safety budgets
remain required. Backend JSON distinguishes `passed` (the enforced policy) from
`performancePassed` (every measured target met); misses appear as warnings and
in a per-sample CI summary. Missing or nonfinite measurements cannot be waived.
Plain `--enforce-budgets` remains strict for every target on a controlled host.

## Recorded reference runs

The [28 October 2026 CI run](https://github.com/ABDELLAH-Hallou/vita-tree/actions/runs/40689709630)
passed all seven jobs, including three independent sustained samples, with the
original budgets unchanged. Server jobs used Python 3.12.15 and four logical
CPUs; the real-PDF job used PDFTeX 1.40.25 / TeX Live 2023. Full machine, fixture,
code and report hashes are in the JSON evidence linked above.

| Server profile | Attempts | Poll p95 | Local orchestration p95 | Peak server RSS |
| --- | ---: | ---: | ---: | ---: |
| CI / simulated PDF | 16 | 168 ms | 1,228 ms | 45.2 MiB |
| Sustained / EPYC 9V45 | 46 | 796 ms | 5,628 ms | 117.9 MiB |
| Sustained / EPYC 7763, sample 2 | 46 | 1,458 ms | 14,813 ms | 135.7 MiB |
| Sustained / EPYC 7763, sample 3 | 46 | 1,477 ms | 14,793 ms | 123.0 MiB |
| CI / restricted real PDF | 16 | 98 ms | 650 ms | 46.2 MiB |

Every sustained sample observed six live providers in every wave. Each had 33
successful, 11 expected failed and two interrupted attempts, with zero unexpected
failures, executing orphans or leaked clean worktrees. Real compiler-call p95 was
646 ms; simulated PDF timings are excluded from that claim. Browser filtering
p95 was 31.6 ms / 10.1 MiB heap at 250 history entries and 38.7 ms / 13.2 MiB at 2,000.
Both browser jobs observed one poll in flight, no page errors and no idle branch
list mutations. Older EPYC samples were close to the 15-second orchestration
budget. An [unchanged-production-code repeat](https://github.com/ABDELLAH-Hallou/vita-tree/actions/runs/40861183972)
measured 15.638 s on EPYC 7763, missing that target by 638 ms while passing all
safety checks. That miss is retained; the 15-second target is not established as
a reliable bound on shared older runners. These are small synthetic measurements,
not capacity guarantees.

Earlier failed sustained budgets and repeat-host misses are retained in the
same evidence. The fixes shorten history locking, coalesce overlapping reads,
batch fresh metadata and avoid reparsing ineligible completed traces. No
completed history refresh is reused. Separate regression tests
cover writer progress, independent result copies, fresh subsequent reads and
failed-refresh recovery. Process ownership tests cover descendants, timeouts,
abrupt owner death and the separate synthetic generation-check endpoint.

## Commands

Use a fresh output directory on every invocation, from the repository root:

```console
python -m pip install -e ".[test,benchmark]"
python -m playwright install chromium
python tests/run_load_profile.py --profile ci --pdf simulated --output .test-artifacts/load-ci --enforce-budgets
python tests/run_load_profile.py --profile sustained --pdf simulated --output .test-artifacts/load-sustained --enforce-budgets
python tests/run_load_profile.py --profile ci --pdf real --output .test-artifacts/load-real --enforce-budgets
python tests/browser_load_profile.py --profile sustained --output .test-artifacts/load-browser --enforce-budgets
```

Install TeX dependencies explicitly before the real-PDF invocation. The fixture
needs PDFLaTeX with `geometry`, `hyperref` and `tabularx`; the workflow installs
`texlive-latex-extra`. Nothing enables shell escape or installs packages during
compilation. A missing engine/package is a failed real-PDF run, not a simulated
success. Simulated mode uses an explicitly labelled 40 ms stub, which is never
used to claim TeX throughput or PDF visual quality.

`--enforce-budgets` gates timing and resource limits. Without it, safety/scenario
failures still fail; exceeded budgets remain visible in JSON. Run profiles alone
on an otherwise idle machine. Concurrent test suites, antivirus, indexers,
different filesystem placement and shared CI hosts can affect measurements.
The workflow runs each reference profile in a separate job.

## Reading the evidence

`results.json` contains nearest-rank p50/p95/max, every measured request
(including failures/timeouts), expected and actual run outcomes, restart and
shutdown evidence, resource samples summarized by interval, retained storage
size, phase distributions and each budget verdict. The browser report records
dispatch-to-next-paint filtering, long tasks, script/layout/task CPU durations,
heap, DOM size, natural polling and draft preservation.

Viewport screenshots wait for deferred rows to enter the viewport and stop
skipping rendering, then wait for paint frames. Bounding-box visibility alone
does not establish that `content-visibility:auto` content has painted; see
[the rendering visibility check](https://developer.mozilla.org/en-US/docs/Web/API/Element/checkVisibility).

`retainedStorage` covers `runs/`, `checkpoints/` and `job-history/`, not the entire
Git object store, worktrees, source captures, PDFs or diagnostic trace storage.

Measurements cover:

- **Provider wait:** measured fixture sleep, separate from a synchronization
  barrier used to prove that all declared branches really have live providers
  at once. Captured keys are checked using synthetic per-branch canaries.
- **Local subprocess cost:** the execution inspector's structured `subprocess`
  phases include interpreter startup, fixture validation/output and process
  teardown as well as provider wait. They are not inferred from CLI stdout.
- **Orchestration:** run wall time minus subprocess phases and PDF calls. This
  includes locks, Git, staging, validation, checkpoints, publication and local
  scheduling. Nested inspector phases must not be added as independent work.
- **PDF:** compiler calls measured independently, including preflight and Cover
  compilation, with simulated/real mode explicit.
- **HTTP/UI:** polling and submission distributions are separate from run wall
  time; browser costs exclude external driver/network delays. The UI must keep
  one poll in flight, preserve an unsaved draft, and avoid replacing unchanged
  branch lists on every idle poll.

An interrupted provider may have a start record and no final timing record;
these censored calls are counted rather than silently discarded. RSS is not
unique resident memory; summed descendant RSS can double-count shared pages.
50 ms sampling can miss short-lived processes and CPU time, so descendant CPU
is a lower bound. Expected failures are not included in the zero-unexpected-
failure budget, but remain in outcome/error fractions.

Only sanitized JSON and synthetic screenshots are uploaded by CI for 14 days.
The local evidence directory also contains temporary repositories, control
records and session-key canaries; do not publish that directory wholesale.
After the test host has stopped, the entire chosen evidence directory can be
removed. Normal application checkpoint/history retention is unchanged by this
benchmark; retained storage is measured, not silently deleted.

Execution trace cleanup checks age/count/space eligibility before parsing
completed trace bodies. Active/reserved traces stay protected, global size/link
checks still run, and ownership is verified before every deletion. This avoids
reparsing all young completed traces on every unrelated workflow phase.

Application checkpoints still have the existing 7-day, 20-terminal-run and
256-MiB total limits (32 MiB per checkpoint). Active attempts and immediate
resume parents are protected. Cleanup runs at startup, launch and completion,
or through Activity & support; it removes checkpoint copies rather than drafts
or history. See [retry retention](../README.md#resume-a-failed-preparation) and
the [checkpoint implementation](../src/vita_tree/checkpoints.py). The benchmark
does not introduce cleanup of the separately retained source/PDF/trace caches.

## Concurrency, backpressure and recovery

There is **no AI admission queue or automatic concurrency cap**. Different
applications start independent provider processes immediately. One active run
per application is enforced; conflicting edits/duplicate starts return 409.
The declared test concurrency is the number the test launches, not a product
limit. CPU, memory, provider accounts and TeX still impose practical limits.

Capture and publication share the workspace lock. History takes a deep snapshot
of records and redaction context under that lock, then reads review statuses and
formats results outside it. Pending requirement drafts briefly reacquire it to
resolve their application context. Overlapping HTTP readers share one in-flight
history refresh instead of repeating thousands of path checks. Each caller gets
its own result copy. A request arriving after that refresh completes reads review
files again; there is no cache reused across completed refreshes. Followers wait
at most 30 seconds and receive an error if the refresh fails. A shared snapshot
can be one refresh behind ongoing writes; mutation/retry endpoints revalidate
current state. This backpressure never gates AI starts, draft saves or worker
updates. PDF preview compilation has its own serialization lock. HTTP polling
waits for completion before scheduling the next 1.5-second poll, so it does not
pile up requests inside one browser. Multiple browser clients can still create
contention. The stress clients deliberately poll every 750 ms after completion.

Inside each refresh, factual-review discovery scans the namespace once and
applies the existing path/symlink/junction checks to existing UUID directories.
Small shared requirement approval/review files are captured once within that
refresh: at most 128 paths, 256,000 source bytes total, and 64,000 bytes per file.
Larger or more varied metadata uses ordinary fresh reads. Binding records remain
individually validated. No cache survives the refresh, and actions/resume use
their original uncached validation paths. Tests cover changing shared approvals,
invalid-file repair, missing evidence and child/namespace symlink or junction
escapes.
The server does not currently offer fair admission or a bounded HTTP worker
pool; this benchmark does not establish behavior under unbounded client load.

Provider invocations have a 600-second Tree timeout; each TeX pass has a
90-second timeout, and its version probe has a 10-second timeout. Backend
provider retry policy remains Vita CV's responsibility. Tree retries are
explicit, lineage-bearing attempts that reuse only verified matching
checkpoints. A Cover retry must consume the matching adapted source. Removing
a session connection blocks future submissions, while a running job retains
its captured connection until completion. Restart clears session credentials.

Shutdown marks active runs interrupted before cancelling owned provider/TeX
process trees and briefly joining workers. Windows uses a kill-on-close Job
Object; POSIX uses a separate process group plus a parent-liveness pipe. The
command cannot start before ownership is established. This is lifecycle
management, not a sandbox against hostile executables that deliberately escape
their process group. Only processes launched through these owners are covered;
ordinary short Git/version probes retain their existing behavior.

Git push/authentication latency and deliberately detached external services are
outside these profiles; no live repository publication or provider smoke run is
performed by the harness.

Worktrees containing dirty, ignored, external or locked files are intentionally
kept. The test explicitly commits its synthetic outputs before requesting
release; cleanup never force-removes user drafts. A released clean application
must be available to ordinary Git checkout. Atomic publication and stale-input
checks remain mandatory after retries and restarts.

Release verification accepts either direct removal (`clean`) or removal by the
earlier deferred release request (`absent`). Both require the owned folder to be
gone and the branch to be absent from Git's worktree registry; the report records
these checks separately. An `absent` response alone is not proof of cleanup.

Implementation references: [Python subprocess lifecycle](https://docs.python.org/3/library/subprocess.html),
[Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[psutil measurement semantics](https://psutil.readthedocs.io/stable/index.html),
[Chromium performance metrics](https://chromedevtools.github.io/devtools-protocol/tot/Performance/).
