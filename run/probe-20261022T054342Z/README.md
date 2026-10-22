# Hafnia on the six new organizer cameras (2026-10-22)

`scripts/probe_cameras.py`, 18 requests: the six synthetic cameras added on 2026-10-21 plus three organizer cameras
as controls, one full-loop window each (17 s, 05:41:56–05:42:13 UTC, not aligned to the incident), two prompts each
(a neutral description and a one-word incident list). One answer per cell; all rows in `results.json`.

| Camera | Description | One-word class | Right? |
|---|---|---|---|
| `vehicle_breakdown_traffic_queue` | pickup stopped, driver gets out (smoke not mentioned; "traffic continues to flow") | BREAKDOWN | yes |
| `bin_pushed_over_onto_sidewalk` | man approaches the bin, it tips over | OBSTRUCTION | yes |
| `escooter_left_across_sidewalk` | **reversed**: "walks toward a parked scooter, mounts it and rides away" | BREAKDOWN | no |
| `school_gate_break_in_night` | "using a tool to cut through the padlock" | NONE | description yes, class no |
| `person_on_railway_tracks` | steps onto the tracks | TRESPASS | yes |
| `graffiti_on_standing_train` | "spray-painting graffiti on the side of a red train" | VANDALISM | yes (graffiti is vandalism) |
| `vandalism` (control) | throws an object, the window shatters | VANDALISM | yes |
| `traffic_flows_in_the_open_lanes` (control) | closed bus lane, roadworks, normal flow | NONE | yes |
| `busy_street` (control) | dense crowd at night | NONE | yes |

Claim-level audit against the recorded frames: `audit.md` (64 description claims, 51 right; the errors are loop-cut
time reversals, traffic and weather priors, one invented outcome, softened intent).

Reading:
- Hafnia understands these urban scenes far better than the real crime clips of `run/bench-20261018` (0 of 8):
  descriptions right on 5 of 6, the one-word class on 4 of 6, controls 3 of 3.
- The e-scooter error is the loop boundary: the window began with the scooter already lying down and continued with
  the loop's restart (the rider arriving), and Hafnia read it as picking the scooter up. Time order is a known weakness
  of Cosmos Reason; event-centred windows (or a clip that shows "before" and "after" explicitly) should avoid it.
- The break-in is described correctly but classified NONE: as before, a description can catch what a one-word list
  misses, and vice versa; neither alone is reliable.
