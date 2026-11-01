# Prompt experiment: a system prompt and structured prompts on Clearway's clips (2026-10-28)

`scripts/prompt_experiment.py`, 16:05-16:40 UTC, 267 requests (today's count 0 before, 267 after). The question:
the Hafnia gateway's *Advanced Settings* hold a *System Prompt* that is sent before the prompt with every request;
on this machine it had never been set (the Settings API returned no stored value for the group, and nothing in the
repository sets one). Clearway's prompt (`clearway/prompt.py`) is one paragraph of JSON instructions with each
category's definition and what it is not. Hafnia was trained with the system prompt "You are a CCTV traffic
analyst. Validate upstream alerts. Think briefly, then output in JSON format." and an AlertValidation JSON task
(Milestone's article, https://www.milestonesys.com/resources/content/articles/smart-city-video-intelligence/). Does any of that, or a sectioned layout, give better answers on the clips the service
really sends?

## How

- **Test set:** 28 clips the service sent to Hafnia on 2026-10-26 (the three-hour shift) and 2026-10-27 (the
  20-minute run), kept as AVIs in the lens spool: crops around the spot, the direct asks' crops among them. Each
  was labelled by eye from its frames (`TESTSET` in the script): 18 incidents (3 person on the tracks, 2 stalled
  vehicles, 6 obstructions, 2 damage, 5 tampering) and 10 clips that show none, among them the shift's false cards
  (a street crop that had been called STALLED_VEHICLE, a fence called PERSON_ON_TRACKS) and the scooter crop that
  had been "a tree branch" and then NONE on 10-27.
- **Same seconds for every variant:** each clip was played once on `lens_1` (`play`), its recorded span measured
  from its own frames (`lens/clock.py`): 28 of 28 verified, every frame seen, offsets +0.01 to +0.02 s. Every cell
  then asked about those spans (`clips.jsonl`).
- **Cells** (`prompts.json`): system prompt none / trained / clearway (ours: the role, fixed camera, crops, "do not
  guess tools, vehicles or people you cannot see", JSON only) × user prompt current / structured (the same content
  in sections, one category per line, the JSON as a template) / structured_plus (plus context, rules and two new
  fields, `confidence` and `evidence`) / alert (the trained AlertValidation shape: an upstream alert in, confirm or
  discard out). The system prompt was switched through the gateway's Settings API between batches (the PUT must
  carry the whole group; `Gateway.set_system_prompt`) and cleared again at the end (verified: empty).
- **Checks:** the baseline asked twice (A, A2) and once more after the setting was cleared (R), to measure how
  much the answers vary on their own; the trained text put inside the user prompt (I) against the same text as
  the system prompt (E).

## Findings

1. **On this set the prompt the service uses kept all 28 answers, twice** (A and A2, 0 false cards, 0 missed),
   the former false cards and the hard scooter crop included. Every variant lost 4 to 10, far outside the
   baseline's own variation (its category never changed between repeats). **Read this as a comparison between
   prompts, not as an accuracy** (added 2026-10-29). The 28 clips are eight looped scenes: six staged incidents
   seen 2 to 5 times each (the five bolt-cutter clips are one act at one gate, the three person-on-the-tracks
   clips one person at one spot) and, as the negatives, quiet moments of the same loops; nothing in the set looks
   like an incident without being one. Clips 18-28 are the Oct 27 run's spans, the very ones `scripts/reask.py`
   re-asked on 10-27 to choose the prompt's negatives (the graffiti became DAMAGE there), and the Oct 26 clips are
   the same scenes a day earlier: the baseline had two tuning passes on this material and the variants none. The
   repeat (A2) shows stability, not generalisation. The held-out check on real streets the prompt was not written
   against is `run/holdout-20261029/README.md`: there the same prompt made 31 false cards of 39 hard negatives.
2. **Layout alone hurts.** The same words laid out in sections (B) lost 7: four street crops of a car driving
   through became "a silver hatchback is stopped in the middle of the lane" (STALLED_VEHICLE), and a scooter lying
   on the pavement became STALLED_VEHICLE. The one-paragraph prompt says "drives straight through the lane" on the
   same clips.
3. **Context, rules and a confidence field hurt more.** structured_plus (C) lost 7, all false cards; the rule
   "do not guess tools, vehicles or people you cannot see" did not stop invented objects, it produced them: "a
   large fallen tree trunk lies across the roadway" on an empty pavement at night, "a large white inflatable
   object" on a crowd. Only 3 of the 10 empty clips stayed NONE.
4. **A system prompt changes the answers and makes them worse.** The trained text (E, 24 of 28) lost the graffiti
   twice ("a person stands on the platform beside a stationary red train", NONE) and the scooter (STALLED_VEHICLE);
   ours (G, 23 of 28) added four false OBSTRUCTIONs, three of them "a fallen tree trunk" on dark fence crops; the
   two together with structured_plus (H) was the worst cell: 18 of 28, all 10 empty clips called an incident
   ("a metallic fence with pointed tops is lying across the pavement").
5. **The trained AlertValidation shape (D) is a strict verifier, not a classifier:** 0 false cards but 10 of the
   18 incidents discarded ("a person tips a green wheeled bin onto its side, which is a routine disposal action").
   What it confirmed was right (8 of 8), among them all five of the High-priority clips (3 person on the tracks, 2
   stalled vehicles). A possible second opinion for High alarms (investigation item 5), to be tested on more clips.
6. **Confidence is not a signal.** Where the prompt asked for one, every answer said 0.9 or 1.0, right or wrong
   (means 0.96 right, 0.95 wrong; the alert shape 0.95 on all 28). Low values would never arrive to feed an
   escalation.
7. **Wording varies, categories do not.** The baseline's two runs agree word for word on 18 of 28 answers and
   differ by a few words on the rest ("forcing following vehicles to stop" / "forcing vehicles behind to stop");
   the category was the same 28 of 28 times, and 5 of 5 after the setting was cleared. The pilot's note that a
   repeat returns the same words does not hold; a repeat returns the same category.
8. **The system prompt is not just prepended.** The trained text in the user prompt (I) and as the system prompt
   (E) gave the same category 9 of 10 times and the same words once; with the wording noise of 7 that is all the
   test can say. Either way the trained text changes the output format: fenced ```` ```json ```` blocks (E 18 of
   28, I 6 of 10). The baseline itself comes fenced about half the time (A 12, A2 15 of 28), never with prose
   around the JSON; the service's parser takes the first `{...}` and was right every time.
9. **No latency cost either way:** Hafnia's own phase 2.0-3.1 s median in every cell but the first (4.1 s, the
   warm-up after an idle hour); longer answers (390 characters with the two extra fields, 250 without) did not
   take longer.

## What this means for Clearway

- Keep `clearway/prompt.py` as it is and leave the gateway's system prompt empty; the setup script has nothing to
  set there. The plain paragraph with negatives beat every structured, contextual and trained form.
- Do not add a `confidence` field; drop that part of investigation item 6. Escalation has to come from the
  pipeline (a second view or a second window), not from the model's self-report.
- The wording noise is real: an ambiguous crop can be "a tree branch" one day and "a fallen bicycle" (OBSTRUCTION)
  the next, as the scooter crop was. For the categories the ledger acts on, the lever is asking twice about
  different views when the first answer is weak, not another prompt.
- For High-priority categories, the alert shape as a second question is worth a trial: on these clips it confirmed
  5 of 5 and never confirmed a wrong one.

Files: `clips.jsonl` (the test set with its verified spans), `prompts.json` (every text and cell), `results.jsonl`
(every answer with phases and timing), `answers.md` (the answers by clip), `summary.json`, the logs; the tables
below are written by `score`.

<!-- tables: written by prompt_experiment.py score; the text above is kept -->
28 clips from the lens spool, played again on `lens_1` and asked about the same recorded seconds in every cell; 28 scored (18 incidents, 10 with none). One request per clip and cell. See `prompts.json` for the texts, `results.jsonl` for every answer, `answers.md` for the answers by clip.

## Cells

| Cell | System prompt | User prompt | Answers | JSON ok | Right category | False cards (of 10) | Missed (of 18) | Wrong category | Confidence right / wrong | Chars | Seconds (median) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | none | current | 28 of 28 | 28 | **28 of 28** | 0 | 0 | 0 | - | 253 | 6.7 |
| B | none | structured | 28 of 28 | 28 | **21 of 28** | 4 | 1 | 2 | - | 271 | 6.5 |
| C | none | structured_plus | 28 of 28 | 28 | **21 of 28** | 7 | 0 | 0 | 0.96 / 0.95 | 397 | 5.8 |
| D | none | alert | 28 of 28 | 28 | **18 of 28** | 0 | 10 | 0 | 0.95 / 0.95 | 378 | 4.5 |
| I | none | trained_in_user | 10 of 10 | 10 | **9 of 10** | 0 | 1 | 0 | - | 249 | 5.5 |
| E | trained | current | 28 of 28 | 28 | **24 of 28** | 0 | 3 | 1 | - | 250 | 4.4 |
| F | trained | structured_plus | 28 of 28 | 28 | **20 of 28** | 6 | 0 | 2 | 0.96 / 0.95 | 391 | 4.5 |
| G | clearway | current | 28 of 28 | 28 | **23 of 28** | 4 | 0 | 1 | - | 267 | 4.4 |
| H | clearway | structured_plus | 28 of 28 | 28 | **18 of 28** | 10 | 0 | 0 | 0.96 / 0.95 | 394 | 4.5 |
| R | none | current | 5 of 5 | 5 | **5 of 5** | 0 | 0 | 0 | - | 263 | 4.3 |
| A2 | none | current | 28 of 28 | 28 | **28 of 28** | 0 | 0 | 0 | - | 256 | 4.5 |

- Word-for-word identical answers, the trained text in the user prompt (I) against the same text as the system prompt (E): **1 of 10** (same category: 9 of 10).
- Word-for-word identical answers, the baseline asked again after the system prompt was cleared (R) against the baseline (A): **2 of 5** (same category: 5 of 5).
- Word-for-word identical answers, the baseline asked a second time (A2) against the first time (A): **18 of 28** (same category: 28 of 28).

## Category per clip

| # | Clip | Truth | A | B | C | D | I | E | F | G | H | R | A2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 39929_cw-0001-person_on_railway_tr | PERSON_ON_TRACKS | PERSON_ON_TRACKS | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) | PERSON_ON_TRACKS (0.9) | PERSON_ON_TRACKS | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) | PERSON_ON_TRACKS | PERSON_ON_TRACKS |
| 2 | 68961_cw-0002-escooter_left_across | OBSTRUCTION | OBSTRUCTION | **STALLED_VEHICLE** | OBSTRUCTION (0.9) | **NONE** (0.9) | OBSTRUCTION | **STALLED_VEHICLE** | **STALLED_VEHICLE** (1.0) | OBSTRUCTION | OBSTRUCTION (0.9) | OBSTRUCTION | OBSTRUCTION |
| 3 | 93547_cw-0004-school_gate_break_in | NONE | NONE | NONE | NONE (0.9) | NONE (0.9) | NONE | NONE | NONE (0.9) | NONE | **OBSTRUCTION** (0.9) | NONE | NONE |
| 4 | 96829_cw-0007-bin_pushed_over_onto | NONE | NONE | **STALLED_VEHICLE** | **STALLED_VEHICLE** (0.9) | NONE (0.9) | NONE | NONE | **STALLED_VEHICLE** (0.9) | NONE | **STALLED_VEHICLE** (0.9) | NONE | NONE |
| 5 | 71209_cw-0008-vehicle_breakdown_tr | STALLED_VEHICLE | STALLED_VEHICLE | STALLED_VEHICLE | STALLED_VEHICLE (1.0) | STALLED_VEHICLE (0.9) | STALLED_VEHICLE | STALLED_VEHICLE | STALLED_VEHICLE (1.0) | STALLED_VEHICLE | STALLED_VEHICLE (1.0) | STALLED_VEHICLE | STALLED_VEHICLE |
| 6 | 57474_cw-0012-school_gate_break_in | NONE | NONE | NONE | **OBSTRUCTION** (0.9) | NONE (0.9) | NONE | NONE | NONE (0.9) | **OBSTRUCTION** | **OBSTRUCTION** (0.9) |  | NONE |
| 7 | 92754_cw-0014-graffiti_on_standing | DAMAGE | DAMAGE | DAMAGE | DAMAGE (0.9) | **NONE** (0.9) | **NONE** | **NONE** | DAMAGE (0.9) | DAMAGE | DAMAGE (0.9) |  | DAMAGE |
| 8 | 17085_cw-0015-school_gate_break_in | TAMPERING | TAMPERING | TAMPERING | TAMPERING (0.9) | **NONE** (0.9) | TAMPERING | TAMPERING | TAMPERING (0.9) | TAMPERING | TAMPERING (0.9) |  | TAMPERING |
| 9 | 25006_cw-0013-busy_street.avi | NONE | NONE | NONE | **OBSTRUCTION** (0.9) | NONE (0.9) | NONE | NONE | **OBSTRUCTION** (0.9) | **OBSTRUCTION** | **OBSTRUCTION** (0.9) |  | NONE |
| 10 | 98983_cw-0019-bin_pushed_over_onto | OBSTRUCTION | OBSTRUCTION | OBSTRUCTION | OBSTRUCTION (0.9) | **NONE** (0.9) | OBSTRUCTION | OBSTRUCTION | OBSTRUCTION (0.9) | OBSTRUCTION | OBSTRUCTION (1.0) |  | OBSTRUCTION |
| 11 | 88745_cw-0021-bin_pushed_over_onto | OBSTRUCTION | OBSTRUCTION | OBSTRUCTION | OBSTRUCTION (0.9) | **NONE** (0.9) |  | OBSTRUCTION | OBSTRUCTION (0.9) | OBSTRUCTION | OBSTRUCTION (0.9) |  | OBSTRUCTION |
| 12 | 39462_cw-0023-traffic_flows_in_the | NONE | NONE | **STALLED_VEHICLE** | **STALLED_VEHICLE** (0.9) | NONE (0.9) |  | NONE | **STALLED_VEHICLE** (0.9) | NONE | **OBSTRUCTION** (0.9) |  | NONE |
| 13 | 97697_cw-0024-traffic_flows_in_the | NONE | NONE | **STALLED_VEHICLE** | **STALLED_VEHICLE** (0.9) | NONE (0.9) |  | NONE | **STALLED_VEHICLE** (0.9) | NONE | **OBSTRUCTION** (0.9) |  | NONE |
| 14 | 64700_cw-0028-school_gate_break_in | NONE | NONE | NONE | **OBSTRUCTION** (0.9) | NONE (0.9) |  | NONE | **OBSTRUCTION** (0.9) | **OBSTRUCTION** | **OBSTRUCTION** (0.9) |  | NONE |
| 15 | 33995_cw-0031-school_gate_break_in | TAMPERING | TAMPERING | TAMPERING | TAMPERING (0.9) | **NONE** (0.9) |  | TAMPERING | TAMPERING (0.9) | TAMPERING | TAMPERING (0.9) |  | TAMPERING |
| 16 | 77617_cw-0032-escooter_left_across | NONE | NONE | NONE | NONE (0.9) | NONE (0.9) |  | NONE | NONE (0.9) | **OBSTRUCTION** | **OBSTRUCTION** (0.9) |  | NONE |
| 17 | 82319_cw-0033-bin_pushed_over_onto | NONE | NONE | **STALLED_VEHICLE** | **STALLED_VEHICLE** (0.9) | NONE (0.9) |  | NONE | **STALLED_VEHICLE** (0.9) | NONE | **OBSTRUCTION** (0.9) |  | NONE |
| 18 | 61867_cw-0001-bin_pushed_over_onto | OBSTRUCTION | OBSTRUCTION | OBSTRUCTION | OBSTRUCTION (0.9) | **NONE** (0.9) |  | OBSTRUCTION | OBSTRUCTION (1.0) | OBSTRUCTION | OBSTRUCTION (1.0) |  | OBSTRUCTION |
| 19 | 17167_cw-0003-vehicle_breakdown_tr | STALLED_VEHICLE | STALLED_VEHICLE | STALLED_VEHICLE | STALLED_VEHICLE (1.0) | STALLED_VEHICLE (0.9) |  | STALLED_VEHICLE | STALLED_VEHICLE (1.0) | STALLED_VEHICLE | STALLED_VEHICLE (1.0) |  | STALLED_VEHICLE |
| 20 | 85257_cw-0004-person_on_railway_tr | PERSON_ON_TRACKS | PERSON_ON_TRACKS | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) | PERSON_ON_TRACKS (0.9) |  | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) |  | PERSON_ON_TRACKS |
| 21 | 01116_cw-0005-school_gate_break_in | TAMPERING | TAMPERING | TAMPERING | TAMPERING (0.9) | TAMPERING (0.9) |  | TAMPERING | TAMPERING (0.9) | TAMPERING | TAMPERING (0.9) |  | TAMPERING |
| 22 | 01555_cw-0006-escooter_left_across | OBSTRUCTION | OBSTRUCTION | **NONE** | OBSTRUCTION (0.9) | **NONE** (0.9) |  | **NONE** | OBSTRUCTION (0.9) | OBSTRUCTION | OBSTRUCTION (0.9) |  | OBSTRUCTION |
| 23 | 66831_cw-0008-graffiti_on_standing | DAMAGE | DAMAGE | DAMAGE | DAMAGE (0.9) | **NONE** (0.9) |  | **NONE** | DAMAGE (0.9) | **OBSTRUCTION** | DAMAGE (0.9) |  | DAMAGE |
| 24 | 65311_cw-0009-school_gate_break_in | NONE | NONE | NONE | NONE (0.9) | NONE (0.9) |  | NONE | NONE (0.9) | NONE | **OBSTRUCTION** (0.9) |  | NONE |
| 25 | 37185_cw-0010-school_gate_break_in | TAMPERING | TAMPERING | TAMPERING | TAMPERING (0.9) | **NONE** (0.9) |  | TAMPERING | TAMPERING (0.9) | TAMPERING | TAMPERING (0.9) |  | TAMPERING |
| 26 | 62072_cw-0011-person_on_railway_tr | PERSON_ON_TRACKS | PERSON_ON_TRACKS | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) | PERSON_ON_TRACKS (0.9) |  | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) | PERSON_ON_TRACKS | PERSON_ON_TRACKS (1.0) |  | PERSON_ON_TRACKS |
| 27 | 01036_cw-0012-escooter_left_across | OBSTRUCTION | OBSTRUCTION | **STALLED_VEHICLE** | OBSTRUCTION (0.9) | OBSTRUCTION (0.9) |  | OBSTRUCTION | **STALLED_VEHICLE** (0.9) | OBSTRUCTION | OBSTRUCTION (0.9) |  | OBSTRUCTION |
| 28 | 65659_cw-0013-school_gate_break_in | TAMPERING | TAMPERING | TAMPERING | TAMPERING (0.9) | TAMPERING (0.9) |  | TAMPERING | TAMPERING (0.9) | TAMPERING | TAMPERING (0.9) |  | TAMPERING |

Bold: a category that differs from the truth. The number in brackets is the answer's own confidence where the prompt asked for one.

