# Claim-level audit of the 18 answers (2026-10-22)

Reference: the recorded frames of the exact window Hafnia received (05:41:56–05:42:13 UTC, exported at 2 fps with
`Get-Snapshot`, `frames/<camera>.jpg`; git-ignored). Each description is split into atomic claims, each claim judged
against the frames. Judge: Claude (Opus) from 2 fps stills, so fast motion and small details (brake lights, distant
people) are judged less surely. One answer per cell. Every window is one loop long but not aligned to the incident, so
each contains a **loop cut**: the incident's aftermath, a jump back to the start, then the incident.

## Descriptions: 64 claims, 51 right (80%), 13 wrong

| Camera | What the window shows (in order) | Wrong claims | Right / total |
|---|---|---|---|
| `vehicle_breakdown_traffic_queue` | pickup drives, smoke from the bonnet, stops in its lane mid-block, a red car stops behind it, driver gets out and stands in the road; loop cut | "in the middle of the intersection" (mid-block lane); "traffic in the adjacent lanes continues to flow steadily" (the car behind stops; no adjacent traffic). Omits the smoke and the queue | 5 / 7 |
| `bin_pushed_over_onto_sidewalk` | bin already lying, man walks off; loop cut; man walks to the bin, grips it, tips it over deliberately, walks off | "attempts to lift it" (he tips it over on purpose: intent turned into an accident); "steps back, observing it" (he walks away) | 7 / 9 |
| `escooter_left_across_sidewalk` | scooter already lying across the sidewalk, man walks away; loop cut; man rides in, stops, lays the scooter down, walks away | "walks … toward a parked electric scooter"; "then mounts it and rides away"; "briefly stopped … before the rider departs": **the story is told in the order the frames were cut, i.e. reversed**. Omits the scooter left lying | 5 / 8 |
| `school_gate_break_in_night` | crouched at the padlock with bolt cutters; loop cut; walks in from the right with the cutters, works on the padlock standing, then crouches | "after successfully cutting the lock" (never shown: invented outcome); "stands, walks to the right, and exits the frame" (he walks *in* from the right: reversed) | 6 / 8 |
| `person_on_railway_tracks` | walking away along the tracks; loop cut; walks onto the platform, sits on the edge with legs over the track, climbs down, walks off along the tracks | "sits on the railings" (sits on the platform edge, then climbs down) | 7 / 8 |
| `graffiti_on_standing_train` | spraying a colourful piece, walks away; loop cut; clean train, walks in with a can, starts spraying | "the platform is wet, indicating recent rain" (dry platform) | 5 / 6 |
| `vandalism` (control) | man throws stones at a window, it cracks; 8 s loop, twice | "wet pavement … wet and reflective" (dry asphalt) | 5 / 6 |
| `traffic_flows_in_the_open_lanes` (control) | roadworks close the bus lane, traffic flows | none (omits the workers in hi-vis, minor) | 7 / 7 |
| `busy_street` (control) | dense crowd at night, no vehicles visible | "vehicles move slowly through the congestion" / "vehicular flow" (no vehicles) | 4 / 5 |

The 13 wrong claims fall into four kinds:

| Kind | Claims | Where |
|---|---|---|
| Time order at the loop cut (the story follows the frame order, which the cut reversed) | 4 | e-scooter ×3, gate (exit instead of entry) |
| Traffic and weather priors (claims a traffic model expects, not seen) | 4 | "wet pavement" ×2, vehicles in a pedestrian-only crowd, "traffic flows steadily" past a breakdown |
| Invented outcome | 1 | gate: "successfully cutting the lock" |
| Intent or detail softened or wrong | 4 | bin "attempts to lift", "observing", "intersection", "sits on the railings" |

## Key fact per incident (what an operator needs)

| Incident | Key fact in the description? |
|---|---|
| breakdown | partly: stopped pickup and driver out, but no smoke and no queue |
| bin | yes, as an accident ("attempts to lift … tips over") rather than a deliberate act |
| e-scooter | **no**: reversed, the scooter is never left |
| gate | yes (tool on the padlock at night), plus an invented outcome |
| railway | yes |
| graffiti | yes |
| vandalism | yes |

## One-word classes: 7 of 9 right

Incident clips 5 of 7 (breakdown, bin as OBSTRUCTION, railway, graffiti as VANDALISM, vandalism); controls 2 of 2.
Wrong: e-scooter BREAKDOWN (consistent with its reversed description: a scooter that stopped), gate NONE
(inconsistent with its own, correct, description).

## Reading for the design

1. **Do not send unaligned windows.** Half the wrong claims and both wrong key facts come from the loop cut (and a
   real camera's equivalent: a window starting mid-event). Centre the window on the change, or show before and after
   explicitly.
2. **Discount free-text weather, surface and "traffic flows" statements.** They come from the model's traffic training,
   not from the clip ("wet" twice on dry ground). Ask for them as separate, checkable questions when they matter.
3. **Ask about observable states, not outcomes.** "Is the padlock still on the gate at the end?" instead of letting the
   model narrate an ending.
4. **Description and one-word class disagree in 2 of 9 cases.** Neither alone is enough for an alarm; a short structured
   checklist (several targeted questions, or one JSON answer) is the next thing to test.
