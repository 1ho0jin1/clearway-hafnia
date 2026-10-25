# The Clearway service, live (F2): first test with Hafnia (2026-10-25)

`scripts/run_clearway.py --answers hafnia --max-requests 10 --minutes 5` on the organizers' six incident cameras, then
`scripts/report_clearway.py`. The service (`clearway/service.py`) runs the whole pipeline live: FrameBridge (10 fps per
camera) → change detector (loops setting, people held back) → SigLIP 2 look → ledger → for each question the event
window (2 s before the change started to 3 s after the report) cropped and played on `lens_1` → one Hafnia request on
`lens_1` with the JSON prompt (`clearway/prompt.py`) → ledger. XProtect alarms are not wired yet (F3): the ledger's
alarm and clear effects are only logged. **10 requests.** Beside each answer the dry run's stand-in records what it
expects (no request), so Hafnia is scored automatically. The dry run before it, with the stand-in answering:
`run/clearway-dry-20261025T083035Z`.

## Result

| Camera | Questions | Asked Hafnia | Card, category | Occurrences on it | Change → card (first) | Recurrence → card (median) | Lens wait (median) |
|---|---|---|---|---|---|---|---|
| Breakdown | 1 | 1 | STALLED_VEHICLE | 22 | 75.6 s | 2.5 s | 59 s |
| Bin | 5 | 3 | OBSTRUCTION | 18 | 55.8 s | 1.4 s | 110 s |
| E-scooter | 2 | 2 | OBSTRUCTION | 9 | 35.5 s | 2.3 s | 45 s |
| Gate | 5 | 2 | TAMPERING | 24 | 85.0 s | 1.7 s | 101 s |
| Tracks | 1 | 1 | PERSON_ON_TRACKS | 2 | 49.0 s | 1.6 s | 31 s |
| Graffiti | 1 | 1 | DAMAGE | 20 | 67.7 s | 1.4 s | 50 s |
| **Total** | **15** | **10** | **6 of 6 right** | 95 | 36–85 s | 1.4–2.5 s | |

Questions not asked: 4 stopped by the run cap (by design), 1 lost to a lens-client error (below). 9.8–9.9 fps per
camera, no frame dropped. Every answer was valid JSON; Hafnia took 8–19 s per request (median about 10 s).

**Hafnia against the stand-in: 9 of 10 agree.** The one difference is the gate (`cw-0010`): Hafnia said NONE ("a
metallic fence with pointed tops remains stationary"), the stand-in TAMPERING only because the clip's time overlapped
the break-in. The crop shows the fence, not the person (people are held back by design), so Hafnia's NONE is the
honest answer for that crop; the gate needs its person trigger (F11). Details are as before: plausible, sometimes
wrong (the graffiti's "where" is pavement, not platform; not checked against the frames here).

## Reading

- **The pipeline works live, end to end: one card per incident, each with the right category and owner, from 10
  requests.** Every later occurrence is recognised without a request and carded in 1.4–2.5 s.
- **The first card is slow: 36–85 s after the change.** Hafnia is about 10 s of that; the rest is the lens. All six
  incidents' first occurrences arrive within about 40 s, every question plays its clip on the one lens camera in turn
  (about 9 s each), and pieces of a first occurrence reported more than 3 s apart are separate questions (the bin and
  the gate asked 5 each). More lens cameras, or asking the first piece first, would cut it; a real site rarely sees
  six new incidents in a minute.
- **The run cap was reached at about 2.5 min** by the first occurrences; the 4 questions it stopped were later pieces
  of incidents already carded (bin, gate). The offline replay of the same cameras (`run/ledger-F1`, no loop guard)
  made 11 requests in 5 min; this run 15 questions.

## What the dry runs found and changed

Five dry runs (stand-in answers, no requests) before this one; the last is committed (`run/clearway-dry-20261025T083035Z`:
15 questions, 6 cards, no errors), the others are left out (`clearway-dry-20261025T0755..0823`).

1. **Times in steps of 128 s.** The change detector kept "static since" times in float32: fine offline (time from 0),
   but live times are Unix seconds, where float32 steps by 128 s; clip windows came out 30 s long or negative.
   Now float64 (`tier0/change.py`).
2. **4.3 fps instead of 10.** One thread could not keep up with six cameras (28 ms per frame). The detector's channel
   maximum (`.max(axis=2)`, a slow numpy reduction) is replaced by exact element-wise maxima (13 → 6 ms per frame,
   identical reports on four clips), and each camera has its own thread (YOLO and SigLIP share the GPU behind a lock):
   9.8–9.9 fps, no drops, about 0.2 s behind live.
3. **The gate asked 11 times instead of 2.** The ledger forgot looks: an incident kept only its last 8, so after 24
   occurrences at one spot the looks of its other spots were gone; and a merge took the merged incident's looks but not
   its box. Looks are now kept diverse (when full, the older of the two most alike goes) and a merge takes the box
   (`clearway/ledger.py`); the offline replay of all 15 clips is unchanged (38 requests, same cards, none missed).
4. **Questions lost their frames.** With 4 workers, questions waited behind the lens for more than the 90 s of
   frames kept per camera. Now 32 workers: each question captures its clip as soon as its window has passed.
5. **Starting in mid-loop.** The detector's warm-up background then held part of the incident: 13 of 17 questions
   came in the first loop, and on two cameras the changes never closed. The test harness now starts each looped
   camera's detector at the start of its loop, as the offline replay did (a real camera is watching before an
   incident happens); the gate's stream never delivers its loop's first 5 frames, so a loop start is also seen as the
   frame index jumping back.
6. **Lens client races** (`lens/client.py`): it read a clip's done record while the publisher was writing it (empty
   file), and, in this live run, while it was being renamed into place (Windows refuses the open:
   `PermissionError`, the lost question). The client retries both; the publisher writes it in one step.
7. **A lost question kept its incident pending for ever** (here the gate's first: 39 occurrences that never got a
   card). The ledger now drops a pending incident whose question failed (`Ledger.on_failed`), so the next occurrence
   is asked anew; a question stopped by the cap stays pending.

## Files

`service.jsonl` (changes, questions, lens spans, answers with Hafnia's full response and the stand-in's expectation,
health), `ledger.jsonl` (the ledger's event log), `changes.jsonl` (every report with its SigLIP look and every closing:
replayable offline with a changed ledger), `incidents.json` (the final state), `summary.json`.
