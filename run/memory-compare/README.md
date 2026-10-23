# Verdict memory with and without SigLIP (2026-10-23)

`scripts/eval_memory.py --persist 1.5 --out run/memory-compare`: every clip of `scripts/eval_change.py` through the
change detector (`tier0/change.py` as of commit 731d18a, the loops setting: 320 px, 0.5%, 1.5 s, people held back),
each change's AFTER crop embedded with SigLIP 2 (`google/siglip2-base-patch16-224`), then five rules replayed in time
order per camera. **No Hafnia requests:** the ground truth stands in for Hafnia (a change inside the clip's incident
span is an incident; for `test_11` only changes at the crash spot). 223 scored changes, 56 of them incidents.
Embeddings and per-change data: `embeddings.npz`; the table: `results-rules.json` (the rules of `scripts/eval_memory.py` replayed on those embeddings); crops in `frames/` (git-ignored).

| Rule | Uses SigLIP | Requests | Saved | Incidents skipped (of 56) |
|---|---|---|---|---|
| `none`: ask about every change | no | 223 | – | 0 |
| `spot`: mute a spot after a rejection (plan A's router) | no | 97 | 57% | **20** |
| `spot_unless_confirmed`: mute a rejected spot unless an incident was confirmed there | no | 133 | 40% | 0 |
| `appearance`: skip what looks like any rejection on the camera, wherever it is | yes | 62 | 72% | **26** |
| **`siglip`: the same spot and the same look (similarity ≥ 0.85, closer to a rejection than to a confirmation)** | yes | **123** | **45%** | **0** |

Per camera (requests / incidents skipped):

| Camera | Changes | Incidents | none | spot | spot unless confirmed | siglip |
|---|---|---|---|---|---|---|
| `vehicle_breakdown_traffic_queue` | 11 | 10 | 11/0 | 8/3 | 11/0 | 11/0 |
| `bin_pushed_over_onto_sidewalk` | 21 | 9 | 21/0 | 8/4 | 21/0 | 14/0 |
| `escooter_left_across_sidewalk` | 8 | 7 | 8/0 | 1/7 | 8/0 | 8/0 |
| `school_gate_break_in_night` | 50 | 24 | 50/0 | 22/6 | 35/0 | 28/0 |
| `graffiti_on_standing_train` | 6 | 6 | 6/0 | 6/0 | 6/0 | 6/0 |
| `city_street_7_condensation_inside_housing` | 25 | 0 | 25/0 | 3/0 | 3/0 | 4/0 |
| `busy_street` | 10 | 0 | 10/0 | 5/0 | 5/0 | 5/0 |
| `test_11` (real) | 17 | 0 | 17/0 | 8/0 | 8/0 | 8/0 |
| Mumbai 02 (real) | 43 | 0 | 43/0 | 21/0 | 21/0 | 22/0 |
| Düsseldorf (real) | 32 | 0 | 32/0 | 15/0 | 15/0 | 17/0 |

The threshold sweep of `tier0.memory.VerdictMemory` itself (`results.json`, `totals`): 0.75 → 120 requests, 0.80 →
122, 0.85 → 123, 0.90 → 130, 0.95 → 152, never an incident skipped. 0.85 was set before the run, not tuned.

## Reading

- **With vs without SigLIP:** the memory cuts requests by 45% without skipping an incident.
- **Against plan A's spot muting,** which saves more but skips 20 of 56 incidents: an incident that comes to rest
  where something harmless was rejected before (the e-scooter, 7 of 8 skipped) is muted. SigLIP asks again because it
  looks different. This is the case for the appearance check.
- **Against the best SigLIP-free rule** (`spot_unless_confirmed`): 10 fewer requests (8%) for the same zero misses,
  mostly on the gate and bin cameras. A real but small margin.
- **Appearance alone is unsafe** (26 skipped): the spot matters as much as the look.
- **Real footage shows no difference yet:** the clips are 3–15 min long and contain no incident at a previously
  rejected spot, so they cannot show the appearance check's advantage; they do show the saving (about half).

## Caveats

- The oracle is the ground truth, not Hafnia. Hafnia's own mistakes would be remembered: a wrongly rejected change
  could make later ones at that spot look "already rejected". Live runs (plan C, M3) must measure it with real answers.
- The synthetic clips repeat exactly every loop, which flatters every memory rule alike.
- One detector setting (loops, 1.5 s). With the real-camera setting (`ChangeParams.real()`) there are fewer changes to
  filter in the first place.
- The incident spans are approximate (from contact sheets; the e-scooter's start corrected once, see
  `scripts/eval_change.py`).

## SigLIP zero-shot on the incidents' AFTER crops (top of 12 descriptions)

All changes in the incident spans, this run (the span also holds changes that are not the incident object, e.g. a
person standing by the bin): bin 11 of 12 "a wheelie bin lying on its side on a pavement"; e-scooter 8 of 9 "an
e-scooter lying on a pavement"; gate 27 of 27 "a person crouching at a gate at night"; tracks 1 of 1; graffiti 7 of 7;
breakdown 7 of 14 "a vehicle broken down in a traffic lane with smoke", 7 "a car or bus stopped in traffic". Useful for
ranking changes when the budget is tight, not a replacement for Hafnia.
