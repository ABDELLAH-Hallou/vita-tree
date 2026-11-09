# Representative-user task study protocol

Status: **protocol only; no participants recruited or sessions conducted**.
Automation cannot establish that applicants understand inheritance, exact model
IDs, credentials or review decisions. This study is a separate release-quality
activity, not a security or accessibility certification.

## Participants and setup

Recruit 6–8 applicants with varied technical experience: at least three who do
not routinely use Git or a terminal, two keyboard-first users, two people who
use a screen reader daily, and one person who uses magnification/text scaling.
These characteristics can overlap. Invite participants to use their usual
browser, assistive technology and input setup; record versions and preferences
without recording a name, email, employer, CV or disability diagnosis.

Use an isolated synthetic CV collection, synthetic job description and named
test models. A local deterministic provider supplies requirements, factual
proposals, a temporary-overload failure, a permanent configuration failure and
final reports/PDFs. Never request personal CVs, real API keys, real provider
logins or paid calls. Explain that credentials shown are inert fixtures. Check
the fixture host cannot contact providers before every session.

Freeze the tested code revision, backend, browser/AT versions and fixture seed.
Reset every participant to the same starting state. Do not start a newer build
mid-study; after fixes, report a separate round. Counterbalance light/dark mode
and the order of temporary/permanent failure tasks. Let participants choose
their comfortable text size, theme and input method; record deviations.

## Consent and moderation (35–45 minutes)

Explain the study tests the product, not the participant. Participation is
voluntary; they may stop or skip any task. Obtain separate permission for any
screen/audio recording. Prefer anonymized notes. Do not collect keystrokes or
record key-entry fields. Keep recordings locally with restricted access, delete
within 30 days, and retain only de-identified findings with consent.

Give the task goal without naming the expected button. Ask the participant to
think aloud if comfortable, but do not interrupt screen-reader speech. Start
timing after reading each goal. After two minutes without progress, ask whether
they want a neutral prompt; record the exact prompt and mark the task assisted.
Stop a task after five minutes or on distress/request. Never silently rescue a
mistake and call it unassisted success.

## Tasks and comprehension probes

| Task goal (read to participant) | Observable completion | Probe after task |
| --- | --- | --- |
| Set the AI model used for this application to the supplied writing model. | Shared model saved; effective inherited steps agree. | Which steps will use it? Is its model ID a friendly name or an exact provider identifier? |
| Use the supplied faster model only to identify job requirements. | Extract override saved, writing steps unchanged. | If you change the shared model next, what happens to Extract? Verify the prediction. |
| Try another Extract model, then leave without keeping that change. | Cancel/Escape discards the trial; saved override remains. | What would Apply have kept? Did Cancel undo a previously applied choice? |
| Add the supplied test API connection from Extract settings, return to your unfinished setup and apply it. | Parent draft retained, correct connection selected, focus recovered. | Where does the key live? What happens after the server restarts? Is a key the same as a model ID? |
| Check the job requirements against the job description and approve them. | Source reached, classification corrected if needed, saved revision approved. | Which items are required, preferred or unclear? Are employment conditions scored as CV skills? |
| Recover from the displayed temporary service failure. | Finds retry and understands reused steps/captured model. | Should you replace a key for overload? Which model will this retry use? |
| Recover from the displayed invalid model/credential failure. | Uses targeted correction rather than endless retries. | Why is this different from overload? Would a generation check use credits? Do not execute one. |
| Review the proposed CV changes: accept the supported wording, keep the original for an uncertain abbreviation, and edit the supplied skill. | Mixed decisions and confirmation; reviewed text reaches final draft; rejected wording absent. | What evidence made that change safe? Was approval performed by you or an automatic policy? |
| Read the final report, open the PDF and return to the application. | Report and PDF reached without losing work. | Which view has exact layout? Can your usual AT read the output in the expected order? |

For keyboard/AT users, observe whether tasks can finish without a pointer,
whether names/roles announce the right action/state, focus order/trapping and
restoration, error announcements, skipped content, repeated/live announcements
and available source/report/PDF alternatives. Ask permission before changing
their AT verbosity or browser settings. Do not interpret silence as approval.

## Recording sheet and decision rules

Before recruiting, record the planned success threshold: at least 80% of all
attempted tasks completed unassisted, with **zero** lost drafts, accidental
credential disclosure, silent branch mix-ups or unintentionally approved
factual changes. With this small purposive sample, report participant counts
and individual task outcomes; do not generalize a population success rate or
calculate a misleading accessibility score.

For each participant/task record: anonymous ID; build/fixture/browser/AT;
theme/zoom/input method; start/end time; success, assisted, failed or skipped;
first wrong turn; errors and recovery; focus/announcement observations; prompt
given; comprehension response; confidence (1–5); and an optional quote approved
for retention. Count abandoned and assisted tasks rather than dropping them.

Triage evidence separately as product defect, misunderstood copy, test-fixture
problem, browser/AT limitation or inconclusive. Reproduce suspected defects;
do not convert a harness mistake into an application bug. Fix demonstrated
blocking problems with regressions, retest with the affected setup and invite
participants to validate consequential changes. Publish anonymized findings
and unresolved coverage, never recordings or personal application data.

Until sessions occur, report **human task success: unavailable**, with the
recruitment and AT coverage still needed. Scripted browser completion is not a
substitute.
