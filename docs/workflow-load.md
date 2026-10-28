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
heap, DOM size, natural polling and draft preservation. Measurements cover:

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

## Concurrency, backpressure and recovery

There is **no AI admission queue or automatic concurrency cap**. Different
applications start independent provider processes immediately. One active run
per application is enforced; conflicting edits/duplicate starts return 409.
The declared test concurrency is the number the test launches, not a product
limit. CPU, memory, provider accounts and TeX still impose practical limits.

Capture and publication share the workspace lock; history formatting also uses
that lock. PDF preview compilation has its own serialization lock. HTTP polling
waits for completion before scheduling the next 1.5-second poll, so it does not
pile up requests inside one browser. Multiple browser clients can still create
contention. The stress clients deliberately poll every 750 ms after completion.
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

Worktrees containing dirty, ignored, external or locked files are intentionally
kept. The test explicitly commits its synthetic outputs before requesting
release; cleanup never force-removes user drafts. A released clean application
must be available to ordinary Git checkout. Atomic publication and stale-input
checks remain mandatory after retries and restarts.

Implementation references: [Python subprocess lifecycle](https://docs.python.org/3/library/subprocess.html),
[Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[psutil measurement semantics](https://psutil.readthedocs.io/stable/index.html),
[Chromium performance metrics](https://chromedevtools.github.io/devtools-protocol/tot/Performance/).
