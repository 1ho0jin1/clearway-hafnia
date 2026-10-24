# The ledger (F1), replayed offline (2026-10-24)

`scripts/eval_ledger.py --loops 20` (event streams), then `--from-events run/ledger-F1` (replay of the final ledger,
`clearway/ledger.py`). No Hafnia requests. Each clip played as its camera plays it (organizer clips 20 loops, about
5 min each; `test_11` and the CC0 streets once), through the change detector (loops setting for the organizer clips,
real-camera setting for the rest), people held back, each report's crop embedded with SigLIP 2.

**Hafnia is replaced by a stand-in**: the camera's category when the lens clip it would get (2 s before the change
started to 3 s after the report) overlaps the incident's lasting state by at least 1 s, NONE otherwise; answers 8 s
after the request (the measured median). The stand-in never errs, so **false cards are not measured here**; that needs
live runs with real answers (M3). The organizer clips get a *loop guard* (test harness only): changes that start within
1 s before to 2 s after a clip restart are dropped, since a real camera never restarts; the "no guard" column shows
the difference.

## Result

| Clip | Minutes | Requests: ask every change | Memory only¹ | **Ledger** | No guard | Cards | Occurrences on them | Incident changes without a card | To card, median |
|---|---|---|---|---|---|---|---|---|---|
| Breakdown | 5.7 | 23 | 4 | **2** | 2 | 1 | 5 | 0 of 23 | 2.6 s |
| Bin | 5.0 | 53 | 3 | **2** | 3 | 1 | 17 | 0 of 53 | 1.7 s |
| E-scooter | 5.0 | 19 | 16 | **2** | 2 | 1 | 17 | 0 of 19 | 2.3 s |
| Gate | 5.0 | 74 | 40 | **1** | 2 | 1 | 24 | 0 of 74 | 2.0 s |
| Tracks | 5.0 | 1 | 1 | **1** | 1 | 1 | 1 | 0 of 1 | 9.5 s |
| Graffiti | 5.0 | 20 | 20 | **1** | 1 | 1 | 20 | 0 of 20 | 1.4 s |
| Vandalism (cracked window) | 2.7 | 0 | 0 | 0 | 0 | 0 | – | – | – |
| Roadworks | 2.7 | 0 | 0 | 0 | 0 | 0 | – | – | – |
| Camera fogging up | 2.7 | 1 | 1 | **1** | 4 | 0 | – | – | – |
| Crowd | 5.2 | 23 | 21 | **5** | 5 | 0 | – | – | – |
| Highway in fog | 13.0 | 0 | 0 | 0 | 0 | 0 | – | – | – |
| `test_11` (real crash; internal only) | 15.0 | 21 | 19 | **18** | 18 | 1 | 1 | 0 of 1 | 59.8 s |
| Mumbai 02 (CC0) | 3.1 | 6 | 4 | **4** | 4 | 0 | – | – | – |
| Mumbai 03 (CC0) | 3.5 | 0 | 0 | 0 | 0 | 0 | – | – | – |
| Düsseldorf (CC0)² | 4.6 | 1 | 1 | **1** | 1 | 0 | – | – | – |
| **Total** | **83** | **242** | **130** | **38** | **43** | **7** | | **0 of 191** | |

¹ Memory only: skip look-alikes of rejections, and group pieces of one occurrence; no recurrences.
² From the earlier run (`run/ledger-F1-real`, before the escalation and merge changes): its one change was asked, not
skipped, and nothing changed since that affects an asked change on a camera with no incident. The final full replay
was stopped twice by Claude Code for low machine memory; the other 14 clips' event streams are saved here
(`events-*.pkl`; `test_11`'s is not committed: AI City licence).

## Reading

- **Six incident cameras, five minutes each: 9 requests and one card per incident**, against 190 if every change were
  asked. Every later occurrence (5 to 24 per camera) is recognised as the same incident: no request, a card in 1.4–2.6 s
  instead of about 8 s. One alarm per incident (quiet period 5 min); the card reopens on each occurrence.
- **No incident change lost** (0 of 191 without a card), with the stand-in.
- **Real footage costs more.** On `test_11` the ledger saves little (18 of 21): its changes are small and the crops
  mostly road, so the verdict memory's skips are made provisional (below) and long-lasting ones are asked after all.
  The crash gets its card 60 s after it started changing; slow for a crash.
- **No cards on scenes without incidents**: crowd 5 requests in 5 min, real streets 0–4 in 3–5 min. With real Hafnia
  answers some of these could become false cards: unmeasured here.

## What the replay found and changed (clearway/ledger.py)

1. One incident gave three cards: the detector reports a tipped bin as its empty place, the bin and its base. **Pieces**
   of one occurrence (near and within 5 s) now join one incident, whose box grows.
2. Incidents never cleared: a small piece that never looks "as before" kept them open. An incident now **clears when its
   largest change closes**.
3. The bin was missed in every later loop: the run-up (a man gripping the bin) was asked first and dismissed, and the
   tipping, reported a second later, joined it. The stand-in now judges **what the clip shows**, not when the change was
   reported; same spot is **containment** (a thin strip inside an incident's box), not IoU; and a piece joins a pending
   incident **only within its clip** (3 s after its report).
4. **The real crash was skipped**: it looked like (SigLIP similarity 0.947) a harmless change Hafnia had rejected at the
   same spot of the highway minutes earlier. On a real camera the road dominates a small crop. Skips are now
   **provisional**: a skipped change still there after 30 s is asked about after all (harmless changes leave, a crash
   stays). Escalated incidents keep their original time, so an old change does not swallow a new one as a piece.
5. A second card per incident camera: the breakdown's look drifted (smoke) and some changes straddled a loop restart. When
   Hafnia's answer names the category of an open or recently cleared incident at the same spot, the new incident is
   **merged** into it: the request is still spent, the card is not doubled.

The event log replays to the same state as the live ledger (round-trip test in the session; replay covers asks,
pieces, recurrences, answers, merges, alarms, clears and operator verdicts). Not yet in the log: skipped changes still
waiting for escalation are lost on a restart.
