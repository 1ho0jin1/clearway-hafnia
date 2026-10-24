# COLLISION regression check (2026-10-24)

`scripts/lens_pilot.py --variants crop`: the six synthetic incident cameras, crop view only, with COLLISION added to
plan C's JSON prompt (gate G3, `run/lens-test_11-20261024T110155Z`). 6 requests. The question: does the new category
pull other incidents towards it (the breakdown above all)? Each camera's event is a new loop occurrence, not the
pilot's recording, so the windows differ from `run/pilot-20261023T162040Z`.

| Camera | Category (with COLLISION) | Same as the pilot? | Summary |
|---|---|---|---|
| Breakdown | STALLED_VEHICLE | yes | "A silver pickup truck stalls in the middle of the lane with its driver-side door open and smoke rising from the engine, blocking traffic as nearby vehicles slow and stop." |
| Bin | OBSTRUCTION | yes | "A person tips a green wheeled bin onto its side on the pavement, leaving it lying there as they walk away." |
| E-scooter | OBSTRUCTION | yes | "The rider loses balance and falls, causing the electric scooter to tip over and lie across the pavement, partially blocking the bike lane." |
| Gate | TAMPERING | yes | "A person in a hoodie crouches and uses a tool to force open a metal gate at night, working steadily without success." |
| Tracks | PERSON_ON_TRACKS | yes | "A person in a red jacket sits on the railway tracks, then stands up and steps back onto the platform." |
| Graffiti | DAMAGE | yes | "A person uses a spray can to paint colorful graffiti on the side of a stationary train at a platform, leaving the artwork visible on the train's exterior." |

**No regression: 6 of 6 categories as before, valid JSON 6 of 6; nothing became COLLISION.**

Summaries checked against the clips: two wrong this time. The e-scooter rider does not fall (he stops and lays the
scooter down: the pilot's crop answer had it right); the person on the tracks does not step back onto the platform (he
sits on the platform edge and climbs down towards the tracks). Whether the new category played a part cannot be told
from one answer each: the windows are new occurrences, and summaries varied between occurrences before. Categories are
stable; summary details are not, which is why the board shows the category and the clip first and marks the summary as
AI-generated.
