# Gate G3: the crash category (2026-10-24)

`scripts/lens_compare.py --camera test_11 --clip data/clips/800x410_test_11 --at 603 --box 140 75 330 180
--variants crop crop_sr --prompt json --asks 1`: 3 requests. The same crash, spot and 6 s window as
`run/lens-test_11-20261023T165151Z` (a white SUV, about 30 px long, spins across the wet lanes and hits the median wall
at about 604 s), now with **COLLISION** in plan C's JSON prompt (`scripts/lens_pilot.py`: "a vehicle hits another
vehicle, a person, a barrier or an object, or spins out of control"). Frames: `frames/` (git-ignored; AI City licence,
internal only).

| View | Category | Summary |
|---|---|---|
| `plain` (full 800×410 frame) | STALLED_VEHICLE | "A white sedan is stalled in the middle lane, blocking traffic and causing vehicles behind it to brake and merge into adjacent lanes." |
| `crop` (bicubic) | **COLLISION** | "A white sedan loses control on the wet roadway, veers sharply into the adjacent lane, and collides with a white SUV, then stalls in the lane." |
| `crop_sr` (Real-ESRGAN) | **COLLISION** | "A white sedan loses control on the wet roadway, veers sharply across lanes, and collides with a white SUV, then stalls in the middle of the lane." |

Claims checked against the frames: the loss of control and the veer across the lanes are right; "collides with a white
SUV" is not supported (the car hits the median wall; no contact with another vehicle is visible in the 2 fps frames);
"sedan" vs SUV is uncertain at this size.

## Reading

- **G3 passes on the crop:** with a crash category, the cropped view names the crash; the full frame still does not.
- **This is the lens's measured value, now twice on the same crash:** 2026-10-21, one-word list: full frame NONE ×2,
  crop ACCIDENT ×2 (`run/lens-test_11-20261021T144445Z`); 2026-10-24, JSON prompt: full frame STALLED_VEHICLE, crop
  COLLISION. On large, close synthetic objects the crop made no difference (`run/pilot-20261023T162040Z`); on a small,
  distant event it decides the answer. One event; an anecdote until more real crashes are tested.
- **Super-resolution again adds nothing** beyond the crop (same category, near-identical sentence).
- **Invented details persist** (the second vehicle), as with the tool types: use the category, not the details.
- Still to check: that COLLISION does not pull in the other incidents (the breakdown above all): the six synthetic
  cameras, crop view, 6 requests.
