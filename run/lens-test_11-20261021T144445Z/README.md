# Lens camera, first test: one crash, plain vs lens (2026-10-21)

`scripts/lens_compare.py --camera test_11 --clip data/clips/800x410_test_11 --at 603 --box 140 75 330 180`, run twice
on consecutive loops of the clip (this folder and `run/lens-test_11-20261021T143551Z`). 6 Hafnia requests in total.
Prompt: the live pipeline's one-word incident question (`incident/verify.py`, `CLASSIFY`). Frames sent and recorded
are in `frames/` (git-ignored: AI City licence, internal tests only).

`test_11` plays AI City 2021 Track 4 training video 91: a wet highway seen from far away; a white SUV spins across the
lanes and hits the median wall (source 602–604 s). In the 800×410 frame the SUV is about 30 px long.

| Variant | What Hafnia got | Run 1 | Run 2 |
|---|---|---|---|
| plain | `test_11`'s own recording, 6 s centred on the crash (as the live pipeline asks) | NONE (4.1 s) | NONE (4.3 s) |
| crop | the same 6 s cropped around the crash region (about 300×170 px) and enlarged to 1280×720, on `lens_1` | ACCIDENT (5.2 s) | ACCIDENT (5.2 s) |
| crop_slow2 | the crop at half speed (each frame twice), 12 s | ACCIDENT (5.2 s) | ACCIDENT (5.2 s) |

- The crash is inside the plain window: the recorded frames (`frames/recorded/`, run 1) show the spin and the impact
  between the window's third and fifth second. Hafnia misses it at full-frame scale, twice.
- The two crashes were found 900.3 s apart, exactly the clip's loop length: frame matching found the same moment.
- The crop box was set by hand from `data/aicity21/review.md`, standing in for tier 0's boxes. Run 1's lens requests
  each caught about 1 s of the neighbouring clip (idle frames; the crop's held last frame). The publisher now starts
  clips on a whole second with a 2 s idle gap between them, and run 2's spans are clean (checked on synthetic clips:
  the recorded span holds exactly the clip and its held tail; recorded times match send times within about 10 ms).

Reading: one event, so an anecdote, not a measurement. But it is the failure the lens is for (a small, distant event)
and it repeats: G0 passes (the lens records and Hafnia answers on it), and E6 is worth running on many windows.
Slow motion adds nothing visible here (both crop variants say ACCIDENT); E6 has to separate the two.

Also measured: after the publisher restarts, XProtect resumes recording `lens_1` about 10 s later; keep it running and
queue clips 15 s after a start.
