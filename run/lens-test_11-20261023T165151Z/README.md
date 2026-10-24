# Small-object test: super-resolution on test_11's distant crash (2026-10-23)

`scripts/lens_compare.py --camera test_11 --clip data/clips/800x410_test_11 --at 603 --box 140 75 330 180
--variants crop crop_sr --prompt json --asks 3`: 9 requests. The same crash and spot as
`run/lens-test_11-20261021T144445Z` (a white SUV, about 30 px long in the 800×410 frame, spins across the wet lanes and
hits the median wall at about 604 s); plan C's JSON prompt (`scripts/lens_pilot.py`, `PROMPT`). Each view asked three
times about the **same** recorded span (the crash comes round only every 15 min), so the repeats measure answer
consistency, not different events. The window contains the spin (checked on `frames/`, git-ignored).

| View | 3 answers |
|---|---|
| `plain` (full 800×410 frame) | STALLED_VEHICLE ×3: "A white sedan is stopped in the middle lane, blocking traffic; vehicles … merge … to bypass" |
| `crop` (bicubic) | STALLED_VEHICLE ×3, the same sentence each time: "A white sedan stalls in the middle lane, blocking traffic and forcing vehicles to merge around it." |
| `crop_sr` (Real-ESRGAN) | identical to `crop`, word for word, ×3 |

## Reading

1. **Super-resolution changed nothing**, even on this small, distant object: the same answer as bicubic, word for
   word, three times. Together with the pilot (no difference on six large objects), there is no evidence that SR helps
   Hafnia. It stays available in `lens/enhance.py` but is not part of the default lens.
2. **The crash is never named.** Nine summaries say "stalls" or "is stopped"; none mentions the spin or the impact.
   Plan C's category list has no crash category, and the answer follows the list: the closest category,
   STALLED_VEHICLE, shapes the summary as well. With the live pipeline's one-word list (which has ACCIDENT) the crop
   gave ACCIDENT twice on 2026-10-21 and the full frame NONE twice. **Fix: add a COLLISION category** to plan C's prompt
   (a crash is the most urgent right-of-way incident) and retest the three views (3 requests).
3. **Asking again about the same span returns the same answer** (crop and crop_sr word for word; plain with small
   wording changes). Repeats must use different windows or events to measure anything; re-asking wastes requests.
4. The full frame is right on the category with the JSON prompt (STALLED_VEHICLE), where the one-word list said NONE
   on 2026-10-21: the definitions in the prompt help more than the crop here.
